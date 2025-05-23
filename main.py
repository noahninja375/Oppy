from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import openai
from openai import OpenAI
import os
import traceback
import tiktoken

'''curl -X POST https://replit.com/@8BitShop/oppy-backend/optimize \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Test prompt"}'
'''

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("secret_key", "dev‑fallback‑secret") 
openai.api_key = os.getenv("my_key")
demo_user = os.getenv("auth_user")
demo_pass = os.getenv("auth_pass")

@app.route('/heartbeat')
def heartbeat():
    return 'OK', 200
  
@app.route("/login", methods=["GET", "POST"])
def login():
  error = None
  if request.method == "POST":
      user = request.form.get("username")
      pw   = request.form.get("password")

      # DEBUG: print incoming vs expected
      print("form username:", repr(user))
      print("form password:", repr(pw))
      print("demo_user envvar:", repr(demo_user))
      print("demo_pass envvar:", repr(demo_pass))

      if user == demo_user and pw == demo_pass:
          session['logged_in'] = True
          return redirect(url_for("index"))
      error = "Invalid credentials"
  return render_template("login.html", error=error)

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))

# Protect these two routes
def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped

@app.route("/")
@login_required
def index():
    return render_template("index.html")






# git remote set-url origin git@github.com:noahninja375/Oppy.git

# Calling a request to our bot to optimzie
@app.route("/optimize", methods=["GET", "POST"])
def optimize_prompt():
  
  try:
    data = request.get_json(force=True)
    print("Received JSON: ", data)
    user_prompt = data.get("prompt", "")

    system_prompt = ("Rewrite this prompt to shorter and cheaper to run on an LLM. Preserve meaning and core specifications, but minimize length and cost. Do not add any new information. Do not remove any information. Do not change the meaning of the prompt. Do not change the tone of the prompt. Do not change the style of the prompt. Do not change the intent of the prompt. No punctuation unless absolutely necessary. Remove unncessary bolding, italics, bullet points, hyphens, and other formatting. If you are given a numerical list with spaces, remove the spaces and condense as much as possible while allowing proper separation for analysis. Do not write in full-sentences when avoidable (articles, extraneous pronouns, etc) are not necessary. Do not waste characters on asterisks. Minimize number of return characters")
    client = OpenAI(api_key=os.getenv("my_key"))
    response = client.chat.completions.create(
      model = "gpt-3.5-turbo",
      messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
      ],
      temperature = 0.5,
      n = 3
    )
  
    op1 = response.choices[0].message.content
    op2 = response.choices[1].message.content
    op3 = response.choices[2].message.content
    if op1 is None or op2 is None or op3 is None:
      return jsonify({"error": "No content returned"}), 500

    optimized_ops = [op1, op2, op3]
    token_ops = []
    dollar_ops = []
    carbon_ops = []
    avg = []
    user_carbon = 0

    user_carbon = len(tiktoken.encoding_for_model("gpt-3.5-turbo").encode(user_prompt)) * 0.015 * 0.37 * 1.11 * 0.01 
    
    for optimized in optimized_ops:
  
      # Rewrite later to get accurate token count, make this actually differentiate between different LLMs (LlaMa, Claude, Gemini, GPT, etc)
      original_len = len(user_prompt.split())
      optimized_len = len(optimized.split())
      
      gpt2_enc = tiktoken.encoding_for_model("text-davinci-003")
      cl100k_enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
      turbo_enc = tiktoken.encoding_for_model("gpt-4")
      davinci_enc = tiktoken.encoding_for_model("gpt-4o")

      a1 = len(gpt2_enc.encode(user_prompt))
      a2 = len(cl100k_enc.encode(user_prompt))
      a3 = len(turbo_enc.encode(user_prompt))
      a4 = len(davinci_enc.encode(user_prompt))

      b1 = len(gpt2_enc.encode(optimized))
      b2 = len(cl100k_enc.encode(optimized))
      b3 = len(turbo_enc.encode(optimized))
      b4 = len(davinci_enc.encode(optimized))

      user_carbon += len(tiktoken.encoding_for_model("gpt-3.5-turbo").encode(optimized)) * 0.015 * 0.37 * 1.11 * 0.01 

      # Percent token savings
      p1 = ((a1-b1) / a1) * 100
      p2 = ((a2-b2) / a2) * 100
      p3 = ((a3-b3) / a3) * 100
      p4 = ((a4-b4) / a4) * 100

      pAvg = (p1 + p2 + p3 + p4) / 4
      
      
      print(len(gpt2_enc.encode(optimized)))
      print(len(cl100k_enc.encode(optimized)))
      print(len(turbo_enc.encode(optimized)))
      print(len(davinci_enc.encode(optimized)))
      
      savings1 = len(gpt2_enc.encode(user_prompt)) - len(gpt2_enc.encode(optimized))
      savings2 = len(cl100k_enc.encode(user_prompt)) - len(cl100k_enc.encode(optimized))
      savings3 = len(turbo_enc.encode(user_prompt)) - len(turbo_enc.encode(optimized))
      savings4 = len(davinci_enc.encode(user_prompt)) - len(davinci_enc.encode(optimized))
 

      
      token_savings = {"DaVinci": f"{savings1} ({p1:.2f}%)", 
                       "GPT 3.5-turbo": f"{savings2} ({p2:.2f}%)", 
                       "GPT 4": f"{savings3} ({p3:.2f}%)", 
                       "GPT 4o": f"{savings4} ({p4:.2f}%)"}
      
      dollar_savings = {"DaVinci": f"${savings1*0.2:.2f}",
                        "GPT 3.5-turbo": f"${(savings2*0.015):.2f}",
                        "GPT 4": f"${(savings3*0.3):.2f}", 
                        "GPT 4o": f"${(savings4*0.1):.2f}"}
  
      # 0.37 * 1.11 * 0.01 * savings1 for DaVinci kg of CO2 saved
      cc = 0.37 * 1.11 * 0.01
      carbon_savings = {"DaVinci": f"{savings1*cc:.2f} kg",
        "GPT 3.5-turbo": f"{(savings2*cc):.2f} kg",
        "GPT 4": f"{(savings3*cc):.2f} kg", 
        "GPT 4o": f"{(savings4*cc):.2f} kg"}
  
      savings = f"${(savings1*(0.02*10)):.2f} (DaVinci), ${(savings2*0.0015*10):.2f} (GPT 3.5-turbo), ${(savings3*0.03*10):.2f} (GPT 4), ${(savings4*0.01*10):.2f} (GPT 4o)"
      token_ops.append(token_savings)
      dollar_ops.append(dollar_savings)
      carbon_ops.append(carbon_savings)
      avg.append(f"{pAvg:.2f}")
      
    # Possibly work on some sort of carbon footprint estimate based on kWh per token. (Jegham et al., May 2025)
    return jsonify({"original_prompt": user_prompt,
                  "optimized_ops": optimized_ops,
                  "token_savings": token_ops,
                  "dollar_savings": dollar_ops,
                  "carbon_savings": carbon_ops,
                  "user_carbon": f"{user_carbon:.2f}",
                   "avg": avg})
  except Exception as E:
    print("‼️ Error in /optimize:", E)
    traceback.print_exc()
    return jsonify({
        "error": str(E),
        "trace": traceback.format_exc().splitlines()[-3:]  # last 3 lines
    }), 500

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=81)
