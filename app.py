from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "secret123"

# Dummy user (demo)
USER = {
    "email": "admin@gmail.com",
    "password": "1234"
}

# HOME
@app.route('/')
def index():
    return render_template('index.html')

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email == USER["email"] and password == USER["password"]:
            session['user'] = email
            return redirect('/dashboard')
        else:
            return "Invalid Login"

    return render_template('login.html')

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    return render_template('dashboard.html', user=session['user'])

# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)