# Team 2

Figma link (Wireframes): https://www.figma.com/design/KQh2sRpxNxaPQl93MTJZRt/TDP-Project-Homepage-Wireframes?node-id=0-1&t=eVFdgBC7EfVeG12K-1


## The FireFighterTracker folder
- **DOCS folder**: Contains all documentation for all of the code and interactions with other aspects of the project
- **SRC folder**:  Contains code for UI and backend of the desktop app
  - assets: Contains images, icons and stylesheets
  - controllers: backend code for data manipulation
  - models: stores data structures
  - views: contains ui pages
  - widgets: widgets displayed on UI pages
- **TESTS folder**: Contains testing for ui backend code etc.

## Tests folder
- tests for pipeline (for now)

## Handling data
- Update map every second or so, act like COD so UAV updates so it looks cleaner
- Workflow:
  - In takes json packet every ...
  - converts/normalises (radar and IMU data scaled to fit) it to map or layout
  - Displays the changes every 1 sec
  
