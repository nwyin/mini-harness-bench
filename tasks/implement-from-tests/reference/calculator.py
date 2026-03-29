class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    def power(self, base, exp):
        return base**exp

    def modulo(self, a, b):
        if b == 0:
            raise ValueError("Cannot modulo by zero")
        return a % b
