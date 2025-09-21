*** Settings ***
Library    keywords.meal_tracker_testing.MealTracker

*** Test Cases ***
Create New User
    ${msg}=    Create New User
    Should Be True    ${msg}    User Creation failed
    Log     Test Case Passed
