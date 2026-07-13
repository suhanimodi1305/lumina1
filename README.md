# lumina1
project running command

Running the project
Since this is a Django project, after pulling updates:

1. Activate your virtual environment :-
d:\lumina1\.venv-1\Scripts\activate.bat

3. Install any new dependencies :-
pip install -r requirements.txt

5. Apply any new migrations :-
python manage.py migrate

7. Run the dev server :-
python manage.py runserver

Common situations
Conflict on push — someone else pushed first. Run git pull origin main first, resolve any conflicts, then push again.
First time on a new machine — clone the repo: git clone https://github.com/your-username/your-repo.git
Check your remote URL: git remote -v
Let me know if you hit any specific errors and I can help debug.
