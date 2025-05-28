from flask import Flask, render_template, request, redirect, url_for, session
import dropbox
import os
import firebase_admin
from firebase_admin import credentials, auth

app = Flask(__name__)
app.secret_key = 'fghgfrthdsjiuygy'  # Replace with a secure secret

# Dropbox setup
DROPBOX_ACCESS_TOKEN = 'sl.u.AFv7Azq6IzHqwpksMlo2SnWEPOy8ljfUIo5UwoUSuE5wy3IawLmfJ4ULlutBMq8pM4ezp8gCq6i2YGsVdnxtqw3whz7SzhM4v6SFBv81Rc4JZF_tD9bJMRT0nw8y70zNG2fuGkACh4JdA76dBPbMEh9BHSU3CJas-oLXyAwa-eCS-b7vsiq3iY83G2JVTqKp38qhtkkqTSmPImBjlIrkHAALQIFdXNhhL3L1FtM2IPhCBkYm1sJdwxpoEsH7DTWmARXHS2UD7tI9p-_85VRuo9d-m7hRmnskNvy59gzV7l7-Z-yKjJ6x9mQaoVv_ZSjkCtMDb0wv0j0cOi-dSjvqxoD7mPIOGxPsb2RRbrnMyfOALgkKzBobe50qvMfPaKZd2L5WBlhCmo1FMVbCTmkO3f6Ea9KGYepvW4tzGmaNkTkwVCrz7ozFX7-NOXr_P0MS4NAKIvIxTmBCbM9lJUUSXBe6x6jD5wXQxF6o8GJeYtWfuKiLz00XQUDUYxGsRr2nEqJxJuQkys8lxOsTHkvdNKVu8dPyIDVnpzIr6lxRwCD0LO8qzMQ_D8G6qXiv39eujQN538R2laE8ooSb_dVlQxTBjZi2PDhw06vyMMJnBaOTXoy5r-zkEwX5NoV6vZR-n0d3HkJShRG_F9KRN870RhxbQWd-FRMHNZ0PiGR27HYIDoVSHJgkdDo8vhm_h8KoAjrfIbU-q00CYesrzdXCcvFV2IOv9LSpfTzteH1zMnzBRFNjZcOlKabvgU5oVnT-pHjJJ2zRmXgPWcuaaGyHxMhm2teZXyd_vEIwk4ChxuRY41hd_8Zd9Kz0EZ7oeveHzWgia7-CmA9KDEgDtVCIdn7MMKrpOTpBWXnJAAAx2yjNkslcOHxnW3LSlp72m8K5OwYjbWw_Nxs0DfzPNJKDM-ZhFPKxJbXv_N-7V_fvFuWZWakInJNcKvftWJAIfyLvdF_aWulkVR6FhhGS5c1I--8pkwftD1RbH9PepkI1bOGqtGYw2kaycH6EqTgND3Dw1A7yeVxwh7m--eYPga6jMdNZ0qW2t41dS8TqjWxvoVMM5BzYApsmPgdrkLKg2VvUMSGGqnIoaZhTy_2jyrxUbmVNW6rciE6p-F53EqBxaiBv8-6yMy5b8ib5lI1HvZckzDlBhjdZ-cyOQponTEiP55q1ELqn_McmR15-9GrqMLrTOMuG_orO--chOo6mpEHXfLAwXiPpIe1X-uYnq22ER1bMOP196KIXDNndD3PSWDIPH6TO-Cdp1F4ULfLLiNzXTZl2EFNoun7RtUvQJ9R87avyp_VQ9lfFJrdQRmClRMHVfOVNf2Zv7lGkNzQbyquFOR0Dx1aZ2coLNhYfrx3cAV0qCH_5OBSkketc6LD9FBIXLfIcYyeUMj2eLWrn2Iv_leeVPoTjSJ7rzQEklPw4djPpn4ah8P_jYi2m7bQGt27Rtg'
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# Firebase Admin SDK setup
cred = credentials.Certificate("config/student-report-portal-firebase-adminsdk.json")
firebase_admin.initialize_app(cred)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    email = session.get('user_email')
    if not email:
        return redirect(url_for('home'))

    # You could also list files from Dropbox for this user
    return render_template('dashboard.html', user_email=email)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['pdf']
    email = session.get('user_email')
    if not file or not email:
        return "Invalid request"

    dropbox_path =f"/Apprentice Training report 2024/{email.replace('@', '_')}_report.pdf"

    dbx.files_upload(file.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)

    return '''
    <html>
    <head>
        <style>
            body {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                font-family: Arial, sans-serif;
                background-color: #f0f0f0;
            }
            .message {
                font-size: 24px;
                font-weight: bold;
                text-align: center;
                background-color: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        <div class="message">
            Thanks! Your report is sent to your manager.<br>It's now safe to close this window.
        </div>
    </body>
    </html>
'''

@app.route('/set-session', methods=['POST'])
def set_session():
    data = request.get_json()
    session['user_email'] = data['email']
    return {'status': 'success'}

if __name__ == '__main__':
    app.run(debug=True)



