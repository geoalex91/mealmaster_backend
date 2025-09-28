*** Settings ***
Library    keywords.meal_tracker_testing.MealTracker

*** Test Cases ***
1_Create_New_User
    ${msg}=    Create New User    user1    user_email1@fake.com    user_password
    Should Be True    ${msg}    User Creation failed
    ${verification_code}    Get Verification Code    user_email1@fake.com
    Should Not Be Empty    ${verification_code}    Verification code not found
    ${is_verified}    Verify User    user_email1@fake.com    ${verification_code}
    Should Be True    ${is_verified}    User Verification failed
    Log     Test Case Passed

2_Create_New_Existing_User
    ${msg}=    Create New User    user1    user_email@fake.com    user_password
    Should Be Equal As Strings    ${msg["detail"]}    User already exists
    Log     Test Case Passed

3_Create_New_User_Existing_Email
    ${msg}=    Create New User    user2    user_email1@fake.com    user_password
    Should Be Equal As Strings    ${msg["detail"]}    User already exists
    Log     Test Case Passed

4_Verify_User_Invalid_Code
    ${msg}=    Create New User    user3    user_3@fake.com    user_password
    Should Be True    ${msg}    User Creation failed
    ${verification_code}    Set Variable    fake_code
    ${is_verified}    Verify User    user_3@fake.com    ${verification_code}
    Should Not Be True    ${is_verified}    User Verification failed
    Log     Test Case Passed

5_Resend_Verification_Code_and_Verify_User
    ${msg}=    Resend Verification    user_3@fake.com
    Should Be True    ${msg}    Resend Verification failed
    ${verification_code}    Get Verification Code    user_3@fake.com
    Should Not Be Empty    ${verification_code}    Verification code not found
    ${is_verified}    Verify User    user_3@fake.com    ${verification_code}
    Should Be True    ${is_verified}    User Verification failed
    Log     Test Case Passed

6_Resend_Verification_Code_Invalid_User
    ${msg}=    Resend Verification    1@email.com
    Should Be Equal As Strings    ${msg["detail"]}    User not found
    Log     Test Case Passed
7_Resend_Verification_Code_Already_Verified_User
    ${msg}=    Resend Verification    user_3@fake.com
    Should Be Equal As Strings    ${msg["detail"]}    User already verified
    Log     Test Case Passed

8_Create_User_Invalid_Email
    ${msg}=    Create New User    new_user3    invalid_email@email.c2m    user_password
    Should Contain    ${msg["detail"]}    Invalid email domain
    Log     Test Case Passed

9_Create_User_code_expiry_timeout
    ${msg}=    Create New User    user4    user_4@fake.com    user_password
    TRY
        Should Not Contain    ${msg["detail"]}    User already exists
    EXCEPT
        Log    detail not found
    END
    ${verification_code}    Get Verification Code    user_4@fake.com
    Should Not Be Empty    ${verification_code}    Verification code not found
    Sleep    ${65}
    ${is_verified}    Verify User    user_4@fake.com    ${verification_code}
    Should Not Be True    ${is_verified}    User was verified, expiry code timeout failed
    Log     Test Case Passed
