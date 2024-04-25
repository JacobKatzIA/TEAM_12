
def calculate_bmr(weight, height, age, gender):
    if gender == 'MAN':
        return (10 * weight) + (6.25 * height) - (5 * age) + 5
    elif gender == 'KVINNA':
        return (10 * weight) + (6.25 * height) - (5 * age) - 161
    else:
        raise ValueError("Felaktig inmatning. Kön måste anges som antingen MAN eller KVINNA")
    

def calculate_daily_calories(weight, height, age, gender, activity_level):
    bmr = calculate_bmr(weight, height, age, gender)
    if activity_level == 1: ##"Ingen eller lite träning"
        calories = bmr * 1.2
    elif activity_level == 2: ##"Träning 1-3 dagar i veckan"
        calories = bmr * 1.375 
    elif activity_level == 3: ##"Träning 4-5 dagar i veckan"
        calories = bmr * 1.55
    elif activity_level == 4: ##"Träning 6-7 dagar i veckan"
        calories = bmr * 1.725 
    elif activity_level == 5: ##"Träning 2 ggr/dag (tung träning)"
        calories = bmr *1.9
    else:
        raise ValueError("Ogiltig aktivitetsnivå")
    return calories
    
def user_input():
    while True:
        try:
            while True:
                weight = input("Vikt i kg: ")
                try:
                    weight = int(weight)
                    if weight <= 0:
                        raise ValueError("Vikten måste vara störra än noll")
                    break
                except ValueError:
                    print("Felaktig inmatning för vikt, försök igen.")
        
            while True:
                height = input("Längd i cm: ")
                try:
                    height = int(height)
                    if height <= 0:
                        raise ValueError("Längden måste vara störra än noll")
                    break
                except ValueError:
                    print("Felaktig inmatning för längd, försök igen.")
        
            while True:
                age = input("Ålder i år: ")
                try:
                    age = int(age)
                    if age <= 0:
                        raise ValueError("Ålderna måste vara större än noll")
                    break
                except ValueError:
                    print("Felaktig inmatning för ålder, försök igen.")
        
            while True:            
                gender = input("Kön (M för man, K för kvinna): ").upper()
                if gender not in ['M', 'K']:
                    print("Ogiltigt kön. Ange 'M' för man eller 'K' för kvinna")
                else:
                    gender = 'MAN' if gender == 'M' else 'KVINNA'
                    break
            
            while True:
                activity_level = input("Ange aktivitetsnivå (1-5): ")
                try:
                    activity_level = int(activity_level)
                    if activity_level < 1 or activity_level > 5:
                        raise ValueError("Aktivitetsnivån måste vara mellan 1-5")
                    break
                except ValueError:
                    print("Felaktig inmatning för aktivitetsnivå, välj mellan 1-5.")
        
            return weight, height, age, gender, activity_level
        
        except ValueError as e:
            print("Felaktig inmatning, försök igen: ") 

def main():
    print()
    print("Här kan du beräkna ditt energibehov/kaloribehov")
    print()
    weight, height, age, gender, activity_level = user_input()
    calories = calculate_daily_calories(weight, height, age, gender, activity_level)
    if calories:
        print("Kcal per dag:", calories)
        

if __name__ == "__main__":
    main()