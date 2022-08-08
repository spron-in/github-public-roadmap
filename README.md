# github-public-roadmap
Collection of scripts to build public roadmaps in GitHub projects

Example: [Percona Operators Roadmap](https://github.com/percona/roadmap/projects/1)

# jira-github.py
This script takes issues from JIRA, creates issues in GitHub and automatically transitions them following JIRA statuses.

What can scipt do now:

* Get issues from JIRA based on the filter ID
* Create issues in the repo and move them to project
* Track JIRA statuses and move cards in the project accordingly
* Once issue is closed in JIRA script will also set the fixVersions label to the issue in Github (if present)

## Usage

```
# PG
export JIRA_FILTER_ID=15413
export JIRA_URI='https://jira.percona.com'

export GIT_USERNAME='spron-in'
export GIT_PASSWORD='a678febe41fd3d814fe5e443a57d9999d6b413e8be'
export GIT_REPO_OWNER='percona'
export GIT_REPO_NAME='roadmap'
export GIT_LABELS='Operators,PG'
export GIT_ROADMAP='Percona Kubernetes Operators Roadmap'

python3 ./jira-github.py
```

## Requirements



## Variables
Some items are hardcoded in the script, but some can be tuned through environment variables.

| Variable       | Description                                                                                                                       | Example                                    |
|----------------|-----------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| GIT_USERNAME   | Github user name                                                                                                                  | spron-in                                   |
| GIT_PASSWORD   | Github password or token                                                                                                          | a678febe41fd3d814fe5e443a57d9999d6b413e8be |
| GIT_REPO_OWNER | Organization that owns the repo                                                                                                   | percona                                    |
| GIT_REPO_NAME  | Repository name                                                                                                                   | roadmap                                    |
| GIT_LABELS     | Comma separated list of labels that are going to be applied to issues when created                                                | Operators,MySQL                            |
| GIT_ROADMAP    | The name of the project which corresponds to the roadmap.  The script will automatically fetch the project ID based on this name. | Percona Kubernetes Operators Roadmap       |
| JIRA_URI       | Your JIRA URI                                                                                                                     | https://jira.percona.com                   |
| JIRA_FILTER_ID | JIRA Filter ID that will be used to fetch issues from JIRA                                                                        | 12345                                      |

## Considerations

* JIRA is the source of truth. Meaning that if you manually add an issue (card) into the project, the script will not detect it and will not process it across the statuses.
* For now statuses mapping between JIRA nad Roadmap are hardcoded in the script. I do it mostly to enforce consistency across various projects and JIRA workflows.



