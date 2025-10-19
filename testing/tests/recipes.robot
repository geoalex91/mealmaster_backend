*** Settings ***
Library    keywords.meal_tracker_testing.MealTracker

*** Test Cases ***
1_Create_New_Recipe
    ${auth_msg}    Login User    user_email1@fake.com    new_password
    Should Be True    ${auth_msg}    Login failed
    ${ingredient_dict}    Create Dictionary    name=Tomato    calories=${20.0}    protein=${1.0}    carbs=${4.0}    fat=${0.2}    fibers=${1.5}    sugar=${2.5}    saturated_fats=${2.5}    category=vegetable
    ${ingredient_msg}    Create Ingredient    ${ingredient_dict}
    Should Be True    ${ingredient_msg}    Ingredient creation failed
    ${ingredient_2_dict}    Create Dictionary    name=Cheese    calories=${100.0}    protein=${6.0}    carbs=${1.0}    fat=${9.0}    fibers=${0.0}    sugar=${0.5}    saturated_fats=${5.0}    category=dairy
    ${ingredient_2_msg}    Create Ingredient    ${ingredient_2_dict}
    ${recipe_ingredient_dict}    Create Dictionary    ingredient_id=Tomato    quantity=100
    ${recipe_ingredient_dict2}    Create Dictionary    ingredient_id=Cheese    quantity=50
    ${recipe_ingredient_list}   Create List    ${recipe_ingredient_dict}    ${recipe_ingredient_dict2}
    ${ingredient_dict1}    Create Dictionary    name=Tomato and cheese salad    description=Fresh tomato    category=vegetable    recipe_ingredients=${recipe_ingredient_list}
    ${recipe_data}    Create Recipe    ${ingredient_dict1}
    Should Be True    ${recipe_data}    Recipe creation failed
    Log    Test Case Passed
