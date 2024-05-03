import psycopg2
from psycopg2 import Error
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'hejhej'

@app.route('/change_credentials', methods=['GET', 'POST'])
def change_credentials():
    if request.method == 'POST':
       current_username = request.form['current_username']
       current_password = request.form['current_password']
       new_username = request.form['new_username']
       new_password = request.form['new_password']

       if not current_username or not current_password or not new_username or not new_password:
          return "Vänligen fyll i alla fält"
       
       if update_credentials(current_username, current_password, new_username, new_password):
          return "Användaruppgifterna har uppdaterats"
       else:
          return "Fel vid uppdatering av användaruppgifter"
       
    return render_template('change_credentials.html')


def update_credentials(current_username, current_password, new_username, new_pasword):
    try:
      connection = psycopg2.connect(
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204")
      
      cursor = connection.cursor()

      cursor.execute("SELECT * FROM members WHERE username = %s AND password = %s", (current_username, current_password))
      user_exists = cursor.fetchone()

      if user_exists:
         cursor.execute("UPDATE members SET username = %s, password = %s WHERE username = %s", (new_username, new_pasword, current_username))
         connection.commit()
         return True
      else:
         return False
      
    except (Exception, Error) as error:
        print("Fel vid uppdatering av användaruppgifter:", error)
        return False
    finally:
        if connection:
           cursor.close()
           connection.close()



def register_member(fullname, username, password, email):
    try:
        connection = psycopg2.connect(
          user="ap2204",
          password="if7fupb5",
          host="pgserver.mau.se",
          port="5432",
          database="ap2204")
      
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM members WHERE email = %s", (email,))
        if cursor.fetchone() is not None:
            print("Användaren finns redan registrerad")
            return False
      
        cursor.execute("SELECT MAX(m_id) FROM members")
        latest_id = cursor.fetchone()[0]

        if latest_id is None:
          latest_id = 0

        next_id = latest_id + 1

        cursor.execute("INSERT INTO members (m_id, fullname, username, password, email) VALUES (%s, %s, %s, %s, %s)",
                      (next_id, fullname, username, password, email))
      
        connection.commit()
        print("Användare registrerad")
        return True

    except (Exception, Error) as error:
        print("Fel vid registrering:", error)
        return False
    finally:
        if connection:
           cursor.close()
           connection.close()
    

@app.route('/register_user')
def register_user():
  return render_template('register_user.html')

@app.route('/submit', methods=['POST'])
def submit():
    fullname = request.form['fullname']
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    if register_member(fullname, username, password, email):
       return redirect('/')
    else:
       return "Registrering misslyckades"



@app.route('/meal', methods=['GET', 'POST'])
def log_meal():
    if request.method == 'POST':
      m_id = request.form['m_id']
      meal_id = request.form['meal_id']
      calories = request.form['calories']
      date = request.form['date']

      connection = psycopg2.connect(
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204"
        )
      if connection:
          try:
            cursor = connection.cursor()

            cursor.execute("INSERT INTO MealCalories (MealID, Calories) VALUES (%s, %s) RETURNING MealCalorieID",
                          (meal_id, calories))
            meal_calorie_id = cursor.fetchone()[0]

            cursor.execute("INSERT INTO MealLog (m_id, MealCalorieID, MealDate) VALUES (%s, %s, %s)",
                          (m_id, meal_calorie_id, date))
            connection.commit()
        
          except (Exception, Error) as error:
            print("Fel vid registrering av måltid:", error)
            return "Din registrering av måltiden misslyckades"
          finally:
            cursor.close()
            connection.close()
      return render_template('meal.html')
      
    connection = psycopg2.connect(
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204"
        )
    if connection:
      try:
        cursor = connection.cursor()
        cursor.execute("SELECT MealID, MealType FROM Meals")
        meal_types = cursor.fetchall()
    
      finally:
        cursor.close()
        connection.close()
    
    return render_template('meal.html', meal_types=meal_types)
  
@app.route('/get_training_log', methods=['POST', 'GET'])
def get_training_log():
  if request.method == 'POST':
    m_id = request.form['m_id']
    date = request.form['date']
    exercise_id = request.form['exercise_id']
    weight = request.form['weight']
    repetitions = request.form['repetitions']
    sets = request.form['sets']
    
    connection = None
    try:
      connection = psycopg2.connect(
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204"
      )
      cursor = connection.cursor()

      cursor.execute('INSERT INTO Workouts (m_id, Date) VALUES (%s, %s) RETURNING WorkoutID',
                     (m_id, date))
      workout_id =cursor.fetchone()[0]

      
      cursor.execute('INSERT INTO WorkoutDetails (WorkoutID, ExerciseID, Weight, Repetitions, Sets) VALUES (%s, %s, %s, %s, %s)',
                     (workout_id, exercise_id, weight, repetitions, sets))
      connection.commit()
      
    except (Exception, psycopg2.Error) as error:
        print("Fel vid inhämtning av träningsloggar:", error)
        return "Kunde inte hämta träningsloggar. Fel: {}".format(error)
    finally:
      if connection:
        cursor.close()
        connection.close()
      return redirect('/get_training_log')
      
  else:
    return render_template('get_training_log.html', workouts=None)

@app.route('/view_workouts/<int:m_id>')
def view_workouts(m_id):
    try:
      connection = psycopg2.connect(
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204"
      )
      cursor = connection.cursor()
      cursor.execute('''
      SELECT Workouts.Date, Exercises.Name, WorkoutDetails.Weight, WorkoutDetails.Repetitions, WorkoutDetails.Sets
      FROM Workouts
      JOIN WorkoutDetails ON Workouts.WorkoutID = WorkoutDetails.WorkoutID
      JOIN Exercises ON WorkoutDetails.ExerciseID = Exercises.ExerciseID
      WHERE Workouts.M_id = %s
      ORDER BY Workouts.Date DESC;              
      ''', (m_id,))
      workouts = cursor.fetchall()
      
      cursor.close()
      connection.close()
      
      return render_template('view_workouts.html', workouts=workouts, m_id=m_id)
    except (Exception, Error) as error:
      print("Fel vid inhämtning av träningsloggar:", error)
      return "Kunde inte hämta träningsloggar."
    finally:
      if connection:
        cursor.close()
        connection.close()

def authenticate_user(username, password):
    try:
        # anslut till databas
        connection = psycopg2.connect(
            user="ap2204",
            password="if7fupb5",
            host="pgserver.mau.se",
            port="5432",
            database="ap2204"
        )
      
        cursor = connection.cursor()
        sql_query = "SELECT username, password FROM members WHERE username = %s AND password = %s"
        cursor.execute(sql_query, (username, password))
        user_info = cursor.fetchone()
        
        # om inget resultat hittades, returnera None
        if user_info is None:
            return None
        return {'username': user_info[0]}
            
    except (Exception, psycopg2.Error) as error:
        print("Gick ej att hämta data från databasen", error)
        return None
    finally: 
        # stäng anslutningen till databasen
        if connection:
            cursor.close()
            connection.close()


@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == 'POST':
    # Användarens inmatning
    username = request.form.get('username')
    password = request.form.get('password')

    # Försök autentisera användaren
    authenticated_user = authenticate_user(username, password)
    
    # Om autentiseringen lyckades, logga in användaren
    if authenticated_user:
      flash('Lyckad inloggning', 'success')
      return redirect(url_for('start'))
    
    else:
      flash('Fel användarnamn eller lösenord. Försök igen.', 'error')
      return redirect(url_for('index'))
  else:
     return render_template('index.html')

@app.route('/start')
def start():
   return render_template('start.html')
   

@app.route('/view_meals/<int:m_id>')
def view_meals(m_id):
    try:
      connection = psycopg2.connect(
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204"
      )
      cursor = connection.cursor()
      cursor.execute('''
      SELECT Meals.Mealtype, MealLog.MealDate, MealCalories.Calories
      FROM MealLog
      JOIN MealCalories ON MealLog.MealCalorieID = MealCalories.MealCalorieID
      JOIN Meals ON MealCalories.MealID = Meals.MealID
      WHERE MealLog.m_id = %s
      ORDER BY MealLog.MealDate DESC;              
      ''', (m_id,))
      meals = cursor.fetchall()
      
      cursor.close()
      connection.close()
      
      return render_template('view_meals.html', meals=meals, user_id=m_id)
    except (Exception, Error) as error:
      print("Fel vid inhämtning av måltidsloggar:", error)
      return "Kunde inte hämta måltidsloggar."
    finally:
      if connection:
        cursor.close()
        connection.close()
        
@app.route('/calculate_calories', methods=['GET', 'POST'])
def calculate_calories():
  calories = None
  if request.method == 'POST':
    weight = request.form['weight']
    height = request.form['height']
    age = request.form['age']
    
    if not (isinstance (weight, str) and weight.isdigit())\
        or not (isinstance(height, str) and height.isdigit())\
        or not (isinstance(age, str) and age.isdigit()):
      flash("Vikt, längd och ålder måste vara numeriska värden.", "error")
      return redirect(url_for('calculate_calories'))
      
    weight = float(weight)
    height = float(height)
    age = int(age)
    
    
    gender = request.form['gender']
    activity_level = int(request.form['activity_level'])
    
    calories = calculate_daily_calories(weight, height, age, gender, activity_level)
    
    return render_template('calculate_calories.html', calories=calories)
  return render_template('calculate_calories.html')
    
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


if __name__ == '__main__':
    app.run(debug=True)


