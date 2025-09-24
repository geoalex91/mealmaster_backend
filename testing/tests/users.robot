*** Settings ***
Library    keywords.meal_tracker_testing.MealTracker

*** Test Cases ***
1_Create_New_User
    ${msg}=    Create New User    new_user    user_email@fake.com    user_password
    Should Be True    ${msg}    User Creation failed
    ${verification_code}    Get Verification Code    user_email@fake.com
    Should Not Be Empty    ${verification_code}    Verification code not found
    ${is_verified}    Verify User    user_email@fake.com    ${verification_code}
    Should Be True    ${is_verified}    User Verification failed
    Log     Test Case Passed

2_Create_New_Existing_User
    ${msg}=    Create New User    dummy    dummy    dummy
    Should Be Equal As Strings    ${msg["detail"]}    User already exists
    Log     Test Case Passed

3_Verify_User_Invalid_Code
    ${msg}=    Create New User    user_second    user_2@fake.com    user_password
    Should Be True    ${msg}    User Creation failed
    ${verification_code}    Set Variable    fake_code
    ${is_verified}    Verify User    user_2@fake.com    ${verification_code}
    Should Not Be True    ${is_verified}    User Verification failed
    Log     Test Case Passed

4_Resend_Verification_Code_and_Verify_User
    ${msg}=    Resend Verification    user_2@fake.com
    Should Be True    ${msg}    Resend Verification failed
    ${verification_code}    Get Verification Code
    Should Not Be Empty    ${verification_code}    Verification code not found
    ${is_verified}    Verify User    user_2@fake.com    ${verification_code}
    Should Be True    ${is_verified}    User Verification failed
    Log     Test Case Passed

5_Resend_Verification_Code_Invalid_User
    ${msg}=    Resend Verification    1@email.com
    Should Be Equal As Strings    ${msg["detail"]}    User not found
    Log     Test Case Passed
6_Resend_Verification_Code_Already_Verified_User
    ${msg}=    Resend Verification    user_2@fake@gmail.com
    Should Be Equal As Strings    ${msg["detail"]}    User already verified
    Log     Test Case Passed
