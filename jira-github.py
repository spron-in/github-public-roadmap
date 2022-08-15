import json
import requests
import re
import os
from jira import JIRA

# Authentication for user filing issue (must have read/write access to
# repository to add issue to)
GIT_USERNAME   = os.getenv('GIT_USERNAME')
GIT_PASSWORD   = os.getenv('GIT_PASSWORD')
GIT_REPO_OWNER = os.getenv('GIT_GIT_REPO_OWNER')
GIT_REPO_NAME  = os.getenv('GIT_GIT_REPO_NAME')

# The repository to add this issue to
GIT_REPO_OWNER = 'percona'
GIT_REPO_NAME  = 'roadmap'

# various git params
GIT_LABELS      = os.getenv('GIT_LABELS')
GIT_LABELS_LIST = GIT_LABELS.split(",")

GIT_ROADMAP     = os.getenv('GIT_ROADMAP')

JIRA_URI       = os.getenv('JIRA_URI')
JIRA_FILTER_ID = os.getenv('JIRA_FILTER_ID')

def get_jira_issues(JIRA_URI, JIRA_FILTER_ID):

    options = {"server": JIRA_URI}
    jira = JIRA(options)

    block_size = 100
    block_num = 0

    glob_issues = []
    while True:
        start_idx = block_num*block_size
        issues = jira.search_issues('filter=%s' % JIRA_FILTER_ID, start_idx, block_size)
        if len(issues) == 0:
            # Retrieve issues until there are no more to come
            break
        for issue in issues:
            glob_issues.append(issue)
        block_num += 1

    return(glob_issues)

class gitHubProc:

    def __init__(self, GIT_USERNAME, GIT_PASSWORD, GIT_REPO_OWNER, GIT_REPO_NAME):

        self.GIT_USERNAME = GIT_USERNAME
        self.GIT_PASSWORD = GIT_PASSWORD
        self.GIT_REPO_OWNER = GIT_REPO_OWNER
        self.GIT_REPO_NAME = GIT_REPO_NAME

    def github_auth(self):
    
        self.session = requests.Session()
        self.session.auth = (self.GIT_USERNAME, self.GIT_PASSWORD)

        return

    def get_issues_in_repo(self):

        headers = {'Accept': 'application/vnd.github.inertia-preview+json'}
        url = 'https://api.github.com/repos/%s/%s/issues?state=all' % (self.GIT_REPO_OWNER, self.GIT_REPO_NAME)
        r = self.session.get(url, headers = headers)
        self.issues = r.json()
        while 'next' in r.links.keys():
            r = self.session.get(r.links['next']['url'],headers = headers)
            self.issues.extend(r.json())

        return(self.issues)

    def get_github_issue(self, issue_id):
    
        headers = {'Accept': 'application/vnd.github.inertia-preview+json'}
        url = 'https://api.github.com/repos/%s/%s/issues/%s' % (self.GIT_REPO_OWNER, self.GIT_REPO_NAME, issue_id)
        r = self.session.get(url, headers = headers)
        issue = r.json()

        return issue

    def edit_github_issue(self, issue_number, data):

        url = 'https://api.github.com/repos/%s/%s/issues/%s' % (self.GIT_REPO_OWNER, self.GIT_REPO_NAME, issue_number)

        r = self.session.patch(url, json.dumps(data))
        if r.status_code == 200:
            print('Successfully updated Issue with issue number %s' % issue_number)
        else:
            print('Could not edit Issue with issue number %s' % issue_number)
            print('Response:', r.content)
        
    def add_label_to_issue(self, issue_number, label):
        url = 'https://api.github.com/repos/%s/%s/issues/%s/labels' % (self.GIT_REPO_OWNER, self.GIT_REPO_NAME, issue_number)
        # Set labels
        data = {"labels":[label]}
        r = self.session.post(url, json.dumps(data))
        if r.status_code == 201:
            print('Successfully set the labels')
            print('Response:', r.content)

        return

    def get_all_cards(self):

        headers = {'Accept': 'application/vnd.github.inertia-preview+json'}

        self.cards_dict = {}
        for column_id in self.columns_dict.values():
            self.cards_dict[column_id] = {}
            url = 'https://api.github.com/projects/columns/%s/cards' % (column_id)
            r = self.session.get(url, headers = headers)
            for card in r.json():
                self.cards_dict[column_id][card['content_url']] = card['id']
            while 'next' in r.links.keys():
                r = self.session.get(r.links['next']['url'],headers = headers)
                for card in r.json():
                    self.cards_dict[column_id][card['content_url']] = card['id']

        return

    def get_card_id_by_issue(self, gh_issue):

        for column_id, column_cards in self.cards_dict.items():
            if gh_issue['url'] in column_cards:
                return(column_id, column_cards[gh_issue['url']])

        return

    def move_github_issue(self, jira, gh_issue):
        # function is going to transition an issue to a correct column in the project
        # and going to assign the correct version if the issue is done

        column_id, card_id = self.get_card_id_by_issue(gh_issue)
        # If usse Status is Done - move to Released status
        # set the version as label
        # close the issue
        if str(jira.fields.status) in ['Done']:
            if column_id != self.columns_dict['Released']:
                self.move_in_project(card_id, self.columns_dict['Released'])
                if len(jira.fields.fixVersions) != 0:
                    self.add_label_to_issue(gh_issue['number'], str(jira.fields.fixVersions[0]))
                self.edit_github_issue(gh_issue['number'], {"state": "closed"})

        elif str(jira.fields.status) in ['In Progress', 'In Packaging', 'In Doc', 'In QA', 'Pending Release', 'Ready For Merge']:
            if column_id != self.columns_dict['Actively working']:
                self.move_in_project(card_id, self.columns_dict['Actively working'])

        # later on we will add In QA column in project. Not relevant for now.
        """
        elif str(jira.fields.status) in ['In QA', 'Pending Release', 'Ready For Merge']:
            if column_id != self.columns_dict['In QA']:
                self.move_in_project(card_id, self.columns_dict['In QA'])
        """

        return

    def match_jira_and_github(self, jira_issues):

        matching = []
        for jira in jira_issues:
            i = 0
            for gh in self.issues:
                if re.search(rf"^\[{jira.key}\].*", gh['title']):
                    self.move_github_issue(jira, gh)
                    i = 1
                    break
            if i == 0:
                matching.append(jira)

        return(matching)


    def list_projects(self):

        headers = {'Accept': 'application/vnd.github.inertia-preview+json'}
        url = 'https://api.github.com/repos/%s/%s/projects' % (self.GIT_REPO_OWNER, self.GIT_REPO_NAME)
        r = self.session.get(url, headers = headers)
        print('Response:', r.content)

    def get_project_id (self, GIT_ROADMAP):

        headers = {'Accept': 'application/vnd.github.inertia-preview+json'}
        url = 'https://api.github.com/repos/%s/%s/projects' % (self.GIT_REPO_OWNER, self.GIT_REPO_NAME)
        r = self.session.get(url, headers = headers)

        self.project_id = None
        projects = r.json()
        for project in projects:
            if project['name'] == GIT_ROADMAP:
                self.project_id = project['id']
                return(self.project_id)

#    print('Response:', r.content)

    def get_project_columns(self):

        headers = {'Accept': 'application/vnd.github.inertia-preview+json'}
        url = 'https://api.github.com/projects/%s/columns' % (self.project_id)
        r = self.session.get(url, headers = headers)

        self.columns_dict = {}
        columns = r.json()
        for column in columns:
            self.columns_dict[column['name']] = column['id']

        return(self.columns_dict)


    def make_github_issue(self, title, body=None, labels=None):
        '''Create an issue on github.com using the given parameters.'''
        # Our url to create issues via POST
        url = 'https://api.github.com/repos/%s/%s/issues' % (self.GIT_REPO_OWNER, self.GIT_REPO_NAME)
        # Create our issue
        issue = {'title': title,
                 'body': body,
                 'labels': labels}
        # Add the issue to our repository
        r = self.session.post(url, json.dumps(issue))
        if r.status_code == 201:
            print('Successfully created Issue "%s"' % title)
            return r.json()['id']
        else:
            print('Could not create Issue "%s"' % title)
            print('Response:', r.content)

    def move_in_project(self, card_id=None, column_id=None, position = 'top'):
        headers = {'Accept': 'application/vnd.github.inertia-preview+json'}
        url = 'https://api.github.com/projects/columns/cards/%s/moves' % (card_id)
        content = {'column_id': column_id,
                   'position': position,
                }
        # Add the issue to the project
        r = self.session.post(url, json.dumps(content), headers = headers)
        if r.status_code == 201:
            print('Successfully moved the card %s' % card_id)
        else:
            print('Could not move the issue')
            print('Response:', r.content)

    def move_to_project(self, issue_id=None):

        column_id = self.columns_dict['Backlog']

        headers = {'Accept': 'application/vnd.github.inertia-preview+json'}
        url = 'https://api.github.com/projects/columns/%s/cards' % (column_id)
        content = {'content_id': issue_id,
                   'content_type': 'Issue',
                }
        # Add the issue to the project
        r = self.session.post(url, json.dumps(content), headers = headers)
        if r.status_code == 201:
            print('Successfully moved the issue')
        else:
            print('Could not move the issue')
            print('Response:', r.content)

issue_body = """
<!-- Please keep this note for the community -->

### Community Note

* Please vote on this issue by adding a :thumbsup: [reaction](https://blog.github.com/2016-03-10-add-reactions-to-pull-requests-issues-and-comments/) to the original issue to help the community and maintainers prioritize this request
* Please do not leave "+1" or "me too" comments, they generate extra noise for issue followers and do not help prioritize the request
* If you are interested in working on this issue or have submitted a pull request, please leave a comment

<!-- Thank you for keeping this note for the community -->

**Tell us about the feature**
"""

gh = gitHubProc(GIT_USERNAME, GIT_PASSWORD, GIT_REPO_OWNER, GIT_REPO_NAME)
gh.github_auth()

gh.get_project_id(GIT_ROADMAP)
gh.get_project_columns()
gh.get_all_cards()

github_issues = gh.get_issues_in_repo()
jira_issues = get_jira_issues(JIRA_URI, JIRA_FILTER_ID)
matching = gh.match_jira_and_github(jira_issues)

for issue in matching:
    title = "[{key}] {summary}".format(key=issue.key, summary=issue.fields.summary)
    print(title)
    body = """
{body}
{description}

[Link to JIRA]({JIRA_URI}/browse/{key})
""".format(body = issue_body, description = issue.fields.description, JIRA_URI = JIRA_URI, key = issue.key)

    issue_id = gh.make_github_issue(title, body, GIT_LABELS_LIST)
    gh.move_to_project(issue_id)
