echo "from flask import Flask" > test_simple.py
echo "app = Flask(__name__)" >> test_simple.py
echo "@app.route('/')" >> test_simple.py
echo "def home(): return 'Server is running!'" >> test_simple.py
echo "app.run(debug=True, port=5000)" >> test_simple.py