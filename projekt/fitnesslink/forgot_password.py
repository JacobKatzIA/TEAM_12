from flask import Flask
from flask_mail import Mail, Message
import os

app = Flask(__name__)

app.config['MAIL_SERVER']='smtp-example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SLL'] = False

mail = Mail(app)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        try:
            connection = psycopg2.connect(
                user="ap2204",
                password="if7fupb5",
                host="pgserver.mau.se",
                port="5432",
                database="ap2204"
            )
            cursor = connection.cursor()
        
            cursor.execute("SELECT * FROM members WHERE email = %s", (email,))
            user = cursor.fetchone()
        
            if  user: ##skapa återställingslänk och skicka den via email
                reset_link = url_for('reset_password', _external=True)
                message = Message('Glömt lösenord', sender='admin@example.com', recipients=[email])
                message.doby = f'Hej! Klicka på länken för att återställa ditt lösenord: {reset_link}'
                mail.send(message)
                return "Ett e-postmeddelande har skickats till dig med instruktioner för att återställa ditt lösenord."
            else:
                return "Kunde inte hitta användaren med den angivning e-postadressen."
        
        except (Exception, Error) as error:
            print("Fel vid återställning av lösenord:", error)
            return "Ett fel uppstod vid återställning av lösenord."
    
        finally:
            if connection:
                cursor.close()
                connection.close()
            
    return render_template('forgot_password.html')
        