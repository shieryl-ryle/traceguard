# QA Test Plan — {{PROJECT_NAME}}

## 1. Gates (run by `test-runner`)
| Gate | Command | Must pass before |
|---|---|---|
| Typecheck | `{{command}}` | every PR |
| Unit | `{{command}}` | every PR |
| E2E | `{{command}}` | merge to main |

## 2. Test cases
| ID | Covers | Steps / assertion | Automated? |
|---|---|---|---|
| TC-001 | F-001, BR-001 | {{assertion}} | {{yes: path / manual}} |

## 3. Exit criteria
- All gates green.
- Every `Must` feature in the PRD has at least one passing TC.
- Every BR-### has a TC or a reviewer check.
