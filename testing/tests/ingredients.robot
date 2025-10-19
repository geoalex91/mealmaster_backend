*** Settings ***
Library    keywords.meal_tracker_testing.MealTracker
Library    String

*** Test Cases ***
1_Create_New_Ingredient
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredient_dict}    Create Dictionary    name=Tomato    calories=${20.0}    protein=${1.0}    carbs=${4.0}    fat=${0.2}    fibers=${1.5}    sugar=${2.5}    saturated_fats=${2.5}    category=vegetable
    ${ingredient_msg}    Create Ingredient    ${ingredient_dict}
    Should Be True    ${ingredient_msg}    Ingredient creation failed
    Log     Test Case Passed
2_Get_All_Ingredients_And_Edit_Ingredient
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredients}=    Get All Ingredients
    Should Not Be Empty    ${ingredients}    No ingredients found
    ${ingredient_id}    Set Variable    ${1}
    ${ingredient_dict}    Create Dictionary    calories=${25}    protein=${1.2}
    ${ingredient_msg}    Update Ingredient    ${ingredient_id}    ${ingredient_dict}
    Should Be True    ${ingredient_msg}    Ingredient update failed
    Log     Test Case Passed

3_Delete_Ingredient
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredients}=    Get All Ingredients
    Should Not Be Empty    ${ingredients}    No ingredients found
    ${ingredient_id}    Set Variable    ${1}
    ${ingredient_msg}    Delete Ingredient    ${ingredient_id}
    Should Be True    ${ingredient_msg}    Ingredient deletion failed
    Log     Test Case Passed
4_Edit_Delete_Nonexistent_Ingredient
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredient_id}=    Get Ingredient ID    Nonexistent
    Should Not Be True    ${ingredient_id}    Ingredient ID should not be found
    ${ingredient_msg}    Delete Ingredient    9999
    Should Contain    ${ingredient_msg["detail"]}    Ingredient not found
    ${ingredient_msg}    Update Ingredient    9999    {"calories": 25, "protein": 1.2}
    Should Contain    ${ingredient_msg["detail"]}    Ingredient not found
    Log     Test Case Passed

5_Create_Ingredient_Invalid_Data_And_Negative_Values
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredient_dict}   Create Dictionary    name=Tomato    calories=${20.0}    protein=${1.0}    carbs=${4.0}
    ${ingredient_msg}    Create Ingredient    ${ingredient_dict}
    Should Contain    ${ingredient_msg["detail"]}    Missing or invalid ingredient data.
    ${ingredient_dict}    Create Dictionary    name=Tomato    calories=${-20.0}    protein=${1.0}    carbs=${4.0}    fat=${0.2}    fibers=${1.5}    sugar=${2.5}    saturated_fats=${2.5}    category=vegetable
    ${ingredient_msg}    Create Ingredient    ${ingredient_dict}
    Should Contain    ${ingredient_msg["detail"]}    Nutritional values must be non-negative.
    Log     Test Case Passed

6_Create_Edit_Delete_ingredient_Unauthenticated
    ${ingredient_dict}    Create Dictionary    name=Tomato    calories=${20.0}    protein=${1.0}    carbs=${4.0}    fat=${0.2}    fibers=${1.5}    sugar=${2.5}    saturated_fats=${2.5}    category=vegetable
    ${ingredient_msg}    Create Ingredient    ${ingredient_dict}
    ${ingredient_id}=    Get Ingredient ID    Tomato
    Should Not Be True    ${ingredient_id}    Ingredient ID should not be found
    ${ingredient_dict}    Create Dictionary    calories=${25}    protein=${1.2}
    ${ingredient_msg}    Update Ingredient    1    ${ingredient_dict}
    Should Not Be True    ${ingredient_msg}    Not authenticated
    ${ingredient_msg}    Delete Ingredient    1
    Should Not Be True   ${ingredient_msg}    Not authenticated
    Log     Test Case Passed

7_Create_ingredient_Duplicate_Name
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredient_dict}    Create Dictionary    name=Tomato    calories=${20.0}    protein=${1.0}    carbs=${4.0}    fat=${0.2}    fibers=${1.5}    sugar=${2.5}    saturated_fats=${2.5}    category=vegetable
    ${ingredient_msg}    Create Ingredient    ${ingredient_dict}
    ${ingredient_msg}    Create Ingredient    ${ingredient_dict}
    Should Contain    ${ingredient_msg["detail"]}    already exists
    Log     Test Case Passed

8_Edit_Delete_Ingredient_Unauthorized_User
    ${auth_msg}    Login User    user3    user_password
    Should Be True    ${auth_msg}    Login 
    ${ingredients}=    Get All Ingredients
    Should Not Be Empty    ${ingredients}    No ingredients found
    ${ingredient_id}    Set Variable    ${1}
    IF    ${ingredient_id}==${False}
        Fail    Ingredient ID not found
    END
    ${ingredient_dict}    Create Dictionary    calories=${25}    protein=${1.2}
    ${ingredient_msg}    Update Ingredient    ${ingredient_id}    ${ingredient_dict}
    Should Contain    ${ingredient_msg["detail"]}    Ingredient not found
    ${ingredient_msg}    Delete Ingredient    ${ingredient_id}
    Should Contain   ${ingredient_msg["detail"]}    Ingredient not found
    Log     Test Case Passed

9_Add_Ingredients_From_JSON_File
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredient_msgs}=    Create Ingredients From File
    Should Be True    ${ingredient_msgs}    Ingredient creation from JSON failed
    Log     Test Case Passed

10_Search_Ingredients
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${search_results}=    Search Ingredients    ros    normal
    Should Not Be Empty    ${search_results}    No ingredients found in search
    ${search_results}    Search Ingredients    anansa    fuzzy
    Should Not Be Empty    ${search_results}    No ingredients found in fuzzy search
    ${search_results}    Search Ingredients    ros    smart
    Should Not Be Empty    ${search_results}    No ingredients found