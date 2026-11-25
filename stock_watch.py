import json, os, pathlib, re
import requests
from bs4 import BeautifulSoup
URL = "https://pizzaofdeath.shop13.makeshop.jp/shopdetail/000000000496/"
SIZES = ["S", "M", "L", "XL", "XXL"]
STATE = pathlib.Path("state.json")
TOPIC = os.environ["NTFY_TOPIC"]  # 推測されにくい文字列にする

def fetch_status():
   r = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
   r.encoding = "euc-jp"  # このサイトはEUC-JP
   soup = BeautifulSoup(r.text, "html.parser")
   status = {}
   for tr in soup.find_all("tr"):
       cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
       if cells and cells[0] in SIZES:
           status[cells[0]] = "売り切れ" not in "".join(cells[1:])
   if not status:
       raise RuntimeError("サイズ表が見つかりません(ページ構造が変わった可能性)")
   return status  # {"S": False, ...} True=在庫あり

def notify(title, msg):
   requests.post(
       f"https://ntfy.sh/{TOPIC}",
       data=msg.encode("utf-8"),
       headers={"Title": title.encode("utf-8"), "Click": URL, "Priority": "high"},
       timeout=30,
   )

def main():
   try:
       now = fetch_status()
   except Exception as e:
       notify("在庫監視エラー", str(e))
       raise
   old = json.loads(STATE.read_text()) if STATE.exists() else {}
   restocked = [s for s, ok in now.items() if ok and not old.get(s, False)]
   if restocked:
       notify("在庫が復活しました", "サイズ: " + ", ".join(restocked))
   STATE.write_text(json.dumps(now, ensure_ascii=False))
   print(now)

if __name__ == "__main__":
   main()
