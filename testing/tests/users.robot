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

10_Login_User_invalid_Credentials
    ${msg}    Login User    user_not_existent    wrong_password
    Should Be Equal As Strings    ${msg["detail"]}    Invalid Credentials
    Log     Test Case Passed
11_Login_user_wrong_password
    ${msg}    Login User    user1    wrong_password
    Should Be Equal As Strings    ${msg["detail"]}    Incorrect password
    Log     Test Case Passed

12_Login_user_not_verified
    ${msg}=    Login User    user_4@fake.com    user_password
    Should Be Equal As Strings    ${msg["detail"]}    User not verified. Please verify your email before logging in.
    Log     Test Case Passed

13_Login_user_success_username
    ${msg}=    Login User    user1    user_password
    Should Be True    ${msg}    Login failed
    Log     Test Case Passed

14_Login_user_success_email
    ${msg}=    Login User    user_email1@fake.com    user_password
    Should Be True    ${msg}    Login failed
    Log     Test Case Passed
15_Change_Password_Success
    ${msg}=    Login User    user_email1@fake.com    user_password
    Should Be True    ${msg}    Login failed
    ${msg}=    Change Password    user1    user_password    new_password
    Should Be True    ${msg}    Password change failed
    ${msg}=    Login User    user1    user_password
    Should Be Equal As Strings    ${msg["detail"]}    Incorrect password
    ${msg}=    Login User    user1    new_password
    Should Be True    ${msg}    Login failed
    ${msg}=    Change Password    user1    wrong_password    new_password
    Should Not Be True    ${msg}    Old password should not be accepted
    Log     Test Case Passed

16_Delete_User_Success
    ${msg}=    Login User    user1    new_password
    Should Be True    ${msg}    Login failed
    ${msg}=    Delete Account    user1    new_password
    Should Be True    ${msg}    User deletion failed
    ${msg}=    Login User    user1    new_password
    Should Contain    ${msg["detail"]}    Invalid Credentials
    Log     Test Case Passed
17_Delete_User_Wrong_Password
    ${msg}=    Login User    user3    user_password
    Should Be True    ${msg}    Login failed
    ${msg}=    Delete Account    user3    new_password
    Should Be Equal As Strings    ${msg["detail"]}    Password is incorrect
    ${msg}=    Delete Account    user3    user_password
    Should Be True    ${msg}    User deletion failed
    Log     Test Case Passed

