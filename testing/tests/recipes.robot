*** Settings ***
Library    keywords.meal_tracker_testing.MealTracker
Library    String


*** Test Cases ***
1_Create_New_Recipe
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredient1_id}    Get Ingredient ID    Rosii
    ${ingredient2_id}    Get Ingredient ID    Morcov
    ${recipe_ingredient_dict}    Create Dictionary    ingredient_id=${ingredient1_id}    quantity=${150}
    ${recipe_ingredient_dict2}    Create Dictionary    ingredient_id=${ingredient2_id}    quantity=${50}
    ${recipe_ingredient_list}   Create List    ${recipe_ingredient_dict}    ${recipe_ingredient_dict2}
    ${season_list}    Create List    summer    autumn
    ${tipe_list}    Create List    salad
    ${recipe_dict}    Create Dictionary    name=Tomato and cheese salad    description=Fresh tomato    
    ...    category=vegetable    image=pathtoimage.jpg    season=${season_list}    type=${tipe_list}    portions=${2}
    ...    cooking_time=${30}    recipe_ingredients=${recipe_ingredient_list}
    ${recipe_data}    Create Recipe    ${recipe_dict}
    Should Be True    ${recipe_data}    Recipe creation failed
    Log    Test Case Passed
2_Create_Recipe_Missing_Fields
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredient1_id}    Get Ingredient ID    Rosii
    ${ingredient2_id}    Get Ingredient ID    Morcov
    ${recipe_ingredient_dict}    Create Dictionary    ingredient_id=${ingredient1_id}    quantity=${150}
    ${recipe_ingredient_dict2}    Create Dictionary    ingredient_id=${ingredient2_id}    quantity=${50}
    ${recipe_ingredient_list}   Create List    ${recipe_ingredient_dict}    ${recipe_ingredient_dict2}
    ${recipe_dict}    Create Dictionary    name=Tomato and carrot salad    description=Fresh tomato
    ...    category=vegetable    season=summer    type=salad    portions=${2}
    ...    cooking_time=${30}    recipe_ingredients=${recipe_ingredient_list}
    ${recipe_data}    Create Recipe    ${recipe_dict}
    Should Be True    ${recipe_data}    Recipe creation failed

3_Create_Recipe_Invalid_Ingredient
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredient1_id}    Get Ingredient ID    Rosii
    ${ingredient2_id}    Get Ingredient ID    Morcov
    ${recipe_ingredient_dict}    Create Dictionary    ingredient_id=${ingredient1_id}    quantity=${150}
    ${recipe_ingredient_dict2}    Create Dictionary    ingredient_id=${ingredient2_id}    quantity=${50}
    ${recipe_ingredient_list}   Create List    ${recipe_ingredient_dict}    ${recipe_ingredient_dict2}
    ${recipe_dict}    Create Dictionary    name=Tomato and cheese salad    description=Fresh tomato
    ...    category=vegetable    season=summer    type=salad    portions=${-2}
    ...    cooking_time=${30}    recipe_ingredients=${recipe_ingredient_list}
    ${recipe_data}    Create Recipe    ${recipe_dict}
    Should Contain    ${recipe_data['detail']}    Cooking time and portions must be non-negative.

4_Create_Recipe_missing_important_fields
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredient1_id}    Get Ingredient ID    Rosii
    ${ingredient2_id}    Get Ingredient ID    Morcov
    ${recipe_ingredient_dict}    Create Dictionary    ingredient_id=${ingredient1_id}    quantity=${150}
    ${recipe_ingredient_dict2}    Create Dictionary    ingredient_id=${ingredient2_id}    quantity=${50}
    ${recipe_ingredient_list}   Create List    ${recipe_ingredient_dict}    ${recipe_ingredient_dict2}
    ${recipe_dict}    Create Dictionary    name=Tomato and cheese salad
    ...    category=vegetable    season=summer    type=salad    portions=${2}
    ...    cooking_time=${30}    recipe_ingredients=${recipe_ingredient_list}
    ${recipe_data}    Create Recipe    ${recipe_dict}
    Should Contain    ${recipe_data['detail']}    Missing or invalid recipe data
5_Create_Recipe_No_Ingredients
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${recipe_dict}    Create Dictionary    name=Tomato and cheese    description=Fresh tomato    
    ...    category=vegetable    image=pathtoimage.jpg    season=summer    type=salad    portions=${2}
    ...    cooking_time=${30}
    ${recipe_data}    Create Recipe    ${recipe_dict}
    Should Contain    ${recipe_data['detail']}    Recipe must have at least one ingredient
    Log    Test Case Passed
6_Create_Already_Existing_Recipe
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredient1_id}    Get Ingredient ID    Rosii
    ${ingredient2_id}    Get Ingredient ID    Morcov
    ${recipe_ingredient_dict}    Create Dictionary    ingredient_id=${ingredient1_id}    quantity=${150}
    ${recipe_ingredient_dict2}    Create Dictionary    ingredient_id=${ingredient2_id}    quantity=${50}
    ${recipe_ingredient_list}   Create List    ${recipe_ingredient_dict}    ${recipe_ingredient_dict2}
    ${recipe_dict}    Create Dictionary    name=Tomato and cheese salad    description=Fresh tomato    
    ...    category=vegetable    image=pathtoimage.jpg    season=summer    type=salad    portions=${2}
    ...    cooking_time=${30}    recipe_ingredients=${recipe_ingredient_list}
    ${recipe_data}    Create Recipe    ${recipe_dict}
    Should Contain    ${recipe_data['detail']}    already exists
    Log    Test Case Passed

7_Edit_Recipe_Cooking_Time
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${recipe_id}    Get Recipe Id By Name    Tomato and cheese salad
    ${updated_recipe_data}    Create Dictionary    cooking_time=${45}
    ${update_msg}    Edit Recipe    ${recipe_id}    ${updated_recipe_data}
    Should Be True    ${update_msg}    Recipe cooking time update failed
    Log    Test Case Passed
8_Edit_recipe
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${recipe_id}    Get Recipe Id By Name    Tomato and cheese salad
    ${ingredient1_id}    Get Ingredient ID    Cirese
    ${ingredient2_id}    Get Ingredient ID    Cartofi
    ${recipe_ingredient_dict}    Create Dictionary    ingredient_id=${ingredient1_id}    quantity=${250}
    ${recipe_ingredient_dict2}    Create Dictionary    ingredient_id=${ingredient2_id}    quantity=${550}
    ${recipe_ingredient_list}   Create List    ${recipe_ingredient_dict}    ${recipe_ingredient_dict2}
    ${updated_recipe_data}    Create Dictionary    name=Cirese si cartofi    description=Cirece cu cartofi
    ...    category=carne    image=pathtoimage_updated.jpg    season=iarna
    ...    type=dulce    portions=${5}    cooking_time=${50}    recipe_ingredients=${recipe_ingredient_list}
    ${update_msg}    Edit Recipe    ${recipe_id}    ${updated_recipe_data}
    Should Be True    ${update_msg}    Recipe update failed
    Log    Test Case Passed
9_Edit_Recipe_user_not_authorized
    ${auth_msg}    Login User    user3    user_password
    Should Be True    ${auth_msg}    Login failed
    ${recipe_id}    Get Recipe Id By Name    Cirese si cartofi
    ${updated_recipe_data}    Create Dictionary    cooking_time=${45}
    ${update_msg}    Edit Recipe    ${recipe_id}    ${updated_recipe_data}
    Should Contain    ${update_msg["detail"]}    Not authorized to edit this recipe
    Log    Test Case Passed

10_Delete_Recipe_user_not_authorized
    ${auth_msg}    Login User    user3    user_password
    Should Be True    ${auth_msg}    Login failed
    ${recipe_id}    Get Recipe Id By Name    Cirese si cartofi
    ${delete_msg}    Delete Recipe    ${recipe_id}
    Should Contain    ${delete_msg["detail"]}    not authorized to delete recipe
    Log    Test Case Passed

11_Delete_Recipe
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${recipe_id}    Get Recipe Id By Name    Cirese si cartofi
    ${delete_msg}    Delete Recipe    ${recipe_id}
    Should Be True    ${delete_msg}    Recipe deletion failed
    Log    Test Case Passed

12_Delete_Nonexistent_Recipe
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${delete_msg}    Delete Recipe    ${999}
    Should Contain    ${delete_msg["detail"]}    Recipe not found
    Log    Test Case Passed

13_Create_Recipes_from_file
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${result}    Create Recipes from File
    Should Be True    ${result}    Recipe creation from file failed
    Log    Test Case Passed

14_Search_Recipe_By_Name
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${id}    Search recipes    Pumpkin    normal
    #Should Be True    ${search_result}    Recipe search by name failed
    ${details}    Get Recipe Details    ${id}
    IF    'Pumpkin' in '${details}'
        Log    Test Case Passed
    ELSE
        Fail    Recipe name does not match search query
    END

15_Seacch_fuzzy_Recipe_By_Name
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${id}    Search recipes    Falaefl    fuzzy
    Should Be True    ${search_result}    Recipe search by name failed
    ${details}    Get Recipe Details    ${id}
    IF    'Falafel' in '${details}'
        Log    Test Case Passed
    ELSE
        Fail    Recipe name does not match search query
    END

16_Search_Recipe_Smart
   ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${id}    Search recipes    Pumpkin    smart
    Should Be True    ${search_result}    Recipe search by name failed
    ${details}    Get Recipe Details    ${id}
    IF    'Pumpkin' in '${details}'
        Log    Test Case Passed
    ELSE
        Fail    Recipe name does not match search query
    END

17_Check_Recipe_usage
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${usage}    Get Recipe Usage Count    Pumpkin Pie
    IF    ${usage} >= ${1}
        Log    Test Case Passed
    ELSE
        Fail    Invalid recipe usage count
    END