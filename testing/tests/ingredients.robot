*** Settings ***
Library    keywords.meal_tracker_testing.MealTracker

*** Test Cases ***
1_Create_New_Ingredient
    ${auth_msg}    Login User    user_email1@fake.com    user_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredient_msg}    Create Ingredient    {"name": "Tomato", "calories": 20, "protein": 1, "carbs": 4, "fats": 0.2, "fiber": 1.5, "sugar": 2.5, "saturated_fats": 2.5, "category: "vegetable"}

2_Get_All_Ingredients_And_Edit_Ingredient
    ${auth_msg}    Login User    user_email1@fake.com    user_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredients}=    Get All Ingredients
    Should Not Be Empty    ${ingredients}    No ingredients found
    ${ingredient_id}=    Get Ingredient ID    Tomato
    Should Not Be Empty    ${ingredient_id}    Ingredient ID not found
    ${ingredient_msg}    Edit Ingredient    ${ingredient_id}    {"calories": 25, "protein": 1.2}
    Should Be True    ${ingredient_msg}    Ingredient update failed
    Log     Test Case Passed

3_Delete_Ingredient
    ${auth_msg}    Login User    user_email1@fake.com    user_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredients}=    Get All Ingredients
    Should Not Be Empty    ${ingredients}    No ingredients found
    ${ingredient_id}=    Get Ingredient ID    Tomato
    Should Not Be Empty    ${ingredient_id}    Ingredient ID not found
    ${ingredient_msg}    Delete Ingredient    ${ingredient_id}
    Should Be True    ${ingredient_msg}    Ingredient deletion failed
    Log     Test Case Passed
4_Edit_Delete_Nonexistent_Ingredient
    ${auth_msg}    Login User    user_email1@fake.com    user_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredient_id}=    Get Ingredient ID    Nonexistent
    Should Be Empty    ${ingredient_id}    Ingredient ID should not be found
    ${ingredient_msg}    Delete Ingredient    9999
    Should Be Equal As Strings    ${ingredient_msg["detail"]}    Ingredient not found
    ${ingredient_msg}    Edit Ingredient    9999    {"calories": 25, "protein": 1.2}
    Should Be Equal As Strings    ${ingredient_msg["detail"]}    Ingredient not found
    Log     Test Case Passed

5_Create_Ingredient_Invalid_Data_And_Negative_Values
    ${auth_msg}    Login User    user_email1@fake.com    user_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredient_msg}    Create Ingredient    {"name": "Tomato", "calories": 20, "protein": 1, "carbs": 4, "fats": 0.2}
    Should Contain    ${ingredient_msg["detail"]}    Missing or invalid ingredient data.
    ${ingredient_msg}    Create Ingredient    {"name": "Tomato", "calories": -20, "protein": 1, "carbs": 4, "fats": 0.2, "fiber": 1.5, "sugar": 2.5, "saturated_fats": 2.5, "category: "vegetable"}
    Should Contain    ${ingredient_msg["detail"]}    Nutritional values must be non-negative.
    Log     Test Case Passed

6_Create_Edit_Delete_ingredient_Unauthenticated
    ${ingredient_msg}    Create Ingredient    {"name": "Tomato", "calories": 20, "protein": 1, "carbs": 4, "fats": 0.2, "fiber": 1.5, "sugar": 2.5, "saturated_fats": 2.5, "category: "vegetable"}
    Should Be Equal As Strings    ${ingredient_msg["detail"]}    Not authenticated
    ${ingredient_id}=    Get Ingredient ID    Tomato
    Should Be Empty    ${ingredient_id}    Ingredient ID should not be found
    ${ingredient_msg}    Edit Ingredient    1    {"calories": 25, "protein": 1.2}
    Should Be Equal As Strings    ${ingredient_msg["detail"]}    Not authenticated
    ${ingredient_msg}    Delete Ingredient    1
    Should Be Equal As Strings    ${ingredient_msg["detail"]}    Not authenticated
    Log     Test Case Passed

7_Create_ingredient_Duplicate_Name
    ${auth_msg}    Login User    user_email1@fake.com    user_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredient_msg}    Create Ingredient    {"name": "Tomato", "calories": 20, "protein": 1, "carbs": 4, "fats": 0.2, "fiber": 1.5, "sugar": 2.5, "saturated_fats": 2.5, "category: "vegetable"}
    Should Be True    ${ingredient_msg}    Ingredient creation failed
    ${ingredient_msg}    Create Ingredient    {"name": "Tomato", "calories": 20, "protein": 1, "carbs": 4, "fats": 0.2, "fiber": 1.5, "sugar": 2.5, "saturated_fats": 2.5, "category: "vegetable"}
    Should Contain    ${ingredient_msg["detail"]}    Ingredient already exists
    Log     Test Case Passed

8_Edit_Delete_Ingredient_Unauthorized_User
    ${auth_msg}    Login User    user_email1@fake.com    user_password
    Should Be True    ${auth_msg}    Login 
    ${ingredients}=    Get All Ingredients
    Should Not Be Empty    ${ingredients}    No ingredients found
    ${ingredient_id}=    Get Ingredient ID    Tomato
    Should Not Be Empty    ${ingredient_id}    Ingredient ID not found
    ${ingredient_msg}    Edit Ingredient    ${ingredient_id}    {"calories": 5, "protein": 8.2}
    Should Be Equal As Strings    ${ingredient_msg["detail"]}    Not authorized to update this ingredient
    ${ingredient_msg}    Delete Ingredient    ${ingredient_id}
    Should Be Equal As Strings    ${ingredient_msg["detail"]}    Not authorized to delete this ingredient
    Log     Test Case Passed



