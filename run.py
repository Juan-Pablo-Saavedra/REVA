"""Punto de entrada para desarrollo: python run.py"""
from sigr import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=False)
