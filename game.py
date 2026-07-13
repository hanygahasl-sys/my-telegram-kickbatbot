import random

number = random.randint(1, 10)
print("Я загадал число от 1 до 10.")

while True:
    guess = int(input("Твой вариант: "))
    
    if guess == number:
        print("Красава! Угадал!")
        break # Это железно остановит программу, когда ты выиграл
    elif guess < number:
        print(">>> МАЛО! Мое число больше.")
    else:
        print(">>> МНОГО! Мое число меньше.")
    
    # Это заставит терминал показать текст прямо сейчас
    print("--------------------", flush=True)