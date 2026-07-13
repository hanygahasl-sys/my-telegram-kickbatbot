import requests
TOKEN = "8959277530:AAFMyFpuMErFFYwO83a36wiIQaEB3eKxoOg"
CHAT_ID = "6683544194" 

url = f"https://api.telegram.org/bot{TOKEN}/getMe"
res = requests.get(url)
print("Проверка бота:", res.json())

url2 = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text=Проверка связи"
res2 = requests.get(url2)
print("Результат отправки:", res2.json())