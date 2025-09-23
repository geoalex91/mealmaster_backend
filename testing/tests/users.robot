*** Settings ***
Library    keywords.meal_tracker_testing.MealTracker

*** Test Cases ***
1_Create New User
    ${msg}=    Create New User    new_user    user_email    user_password
    Should Be True    ${msg}    User Creation failed
    Log     Test Case Passed

2_Create New Existing User
    ${msg}=    Create New User    dummy    dummy    dummy
    Should Be Equal As Strings    ${msg["detail"]}    User already exists
    Log     Test Case Passed
