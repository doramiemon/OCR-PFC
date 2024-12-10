import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
import os
import base64
import requests
from io import StringIO
from io import BytesIO
import _config
import matplotlib.pyplot as plt




#ネットにあげるときは、apiキーを入力させる
# open cv 使う

prompt = """
    入力画像は成分表示の画像です。この画像から、熱量、タンパク質、脂質、炭水化物、4項目のみを抽出して、以下の条件のもとカンマ区切りcsv形式で出力してください。
    ・出力内容はリストに入れて出力しない 
    ・他の日本語は出力しない
    ・金額にカンマは入れない
    ・kcalやgなどの単位を入れない
    ・例 210,7.3,0.6,52.3
    ・「一食あたり」と書かれている場合は、そのまま抽出する。
    ・「g当たり」と書かれている場合は、内容量分として計算する。
    """


def ocr_pdf_to_csv(uploaded_files, output_folder, output_name):
    concat_df = pd.DataFrame([])
    for uploaded_file in uploaded_files:
        # PDFをバイトデータから画像に変換
        


        if uploaded_file.type == "application/pdf":
            image = pdf_to_images(uploaded_file.read())
            base64_image = encode_image(image[0])
            

        # PNGファイルの場合
        elif uploaded_file.type == "image/png" or uploaded_file.type == "image/jpeg":
            image_bytes = uploaded_file.read()
            image_stream = BytesIO(image_bytes)
    
            # Base64エンコード
            base64_image = base64.b64encode(image_stream.read()).decode('utf-8')
            


            

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        content = response.json()['choices'][0]['message']['content']
        
        data = StringIO(content)
        df = pd.read_csv(data, header=None)
        df['ファイル名'] = uploaded_file.name

        concat_df = pd.concat([concat_df, df])

    columns = ["熱量(kcal)","タンパク質(g)","脂質(g)","炭水化物(g)","ファイル名"]
    concat_df.columns = columns
    concat_df = concat_df.reset_index(drop=True)
    print(concat_df)
    output_file = os.path.join(output_folder, output_name)
    concat_df.to_csv(output_file, index=False)
    return output_file, concat_df

def pdf_to_images(pdf_bytes):
    return convert_from_bytes(pdf_bytes)

# Function to encode the image
def encode_image(image):
    # Save the image to a temporary path
    temp_image_path = "temp_image.jpeg"
    image.save(temp_image_path)
    
    with open(temp_image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
def PFC_calculation(calories, protein, fat, carbohydrates):
    
    
       
    
    Ppre = ((protein*4)/calories)*100
    Fpre = ((fat*9)/calories)*100
    Cpre = ((carbohydrates*4)/calories)*100

    total_ratio = Ppre + Fpre + Cpre

    P = (Ppre / total_ratio) * 100
    F = (Fpre / total_ratio) * 100
    C = (Cpre / total_ratio) * 100

    with col1:
        st.write(f"# P: {round(P,1)}%")
        st.write(f"# F: {round(F,1)}%")
        st.write(f"# C: {round(C,1)}%")

    with col2:

            # データの設定
            labels = ["P", "F", "C"]
            sizes = [round(P,1), round(F,1), round(C,1)]
            colors = ["red", "turquoise", "yellow"]

            # Matplotlibで円グラフ作成
            fig, ax = plt.subplots()
            ax.pie(
                sizes,
                labels=labels,
                colors=colors,
                autopct="%1.1f%%",  # パーセンテージ表示
                startangle=90,  # 開始角度を指定
                textprops={"fontsize": 18},  # ラベルの文字サイズ
                labeldistance=1.2,  # ラベルを外側に配置
                pctdistance=0.8  # パーセンテージを内側に配置
            )
            ax.axis("equal")  # 円を正円にする

            # Streamlitに表示
            st.pyplot(fig)

    flag = 0

    if P > 35:
        flag += 1
        st.error("タンパク質過多です。")
        st.write("タンパク質過多になると、腎臓に負担がかかり、腎機能の低下や尿路結石のリスクが増加します。また、必要以上のエネルギーが脂肪として蓄積され、体重増加を招く可能性があります。")

    if F > 30:
        flag += 1
        st.error("脂質過剰です。")
        st.write("脂質過剰になると、肥満や動脈硬化、心疾患のリスクが増加します。特に飽和脂肪酸やトランス脂肪酸を過剰摂取すると、血中コレステロール値が上昇し、生活習慣病の原因となります。")

    if C > 65:
        flag += 1

        st.error("炭水化物過多です。")
        st.write("炭水化物過多は肥満や糖尿病のリスクを高めます。余剰分が脂肪として蓄積され、血糖値の急上昇がインスリン抵抗性を招く可能性があります。適量と質が重要です。")

    if P < 13:
        flag += 1
        st.error("タンパク質不足です。")
        st.write("タンパク質が不足すると、筋力低下や免疫力の低下、貧血、肌や髪の健康悪化などが起こります。成長や回復が遅れるほか、エネルギー不足により疲れやすくなることもあります。")

    if flag <= 0:

        st.success("PFCバランスは適切です。健康的な食生活を続けましょう！")







# OpenAI API Key
#api_key = _config.KEY

with st.sidebar:
    api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    "[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)"
    "[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"

# APP
st.title('PFC balance Application')

st.write(' PFCバランスとは、食事から摂取するカロリーに占める三大栄養素の割合を指します。三大栄養素は、タンパク質（Protein）、脂質（Fat）、炭水化物（Carbohydrate）のことで、これらのバランスを調整することで、健康維持や理想の体づくりをサポートします。一般的な理想比率は、タンパク質13～30％、脂質20～30％、炭水化物50～65％とされますが、個人の目標や活動量によって適した比率は異なります。タンパク質は筋肉の修復や免疫力の維持に、脂質はホルモンの生成やエネルギー供給に、炭水化物は主にエネルギー源として機能します。不適切なバランスは健康リスクを高める可能性があるため、自身の生活スタイルに合ったPFCバランスを意識することが重要です。食事の質も考慮し、栄養価の高い食材を選ぶことが推奨されます。')

uploaded_files = st.file_uploader("Upload PDF files", type=["pdf", "png", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    st.write(f"{len(uploaded_files)} file(s) uploaded.")

    output_folder = os.getcwd() 
    output_filename = "ocr_results.csv"
    
    if st.button('Run OCR'):
        output_file, concat_df = ocr_pdf_to_csv(uploaded_files, output_folder, output_filename)
        st.success(f"OCR completed!")
        
        # 初期データフレームをセッションステートに保存
        st.session_state['df'] = concat_df

    # セッションステートからデータフレームを取得
    if 'df' in st.session_state:
        # 編集可能なデータフレームを表示
        edited_df = st.data_editor(st.session_state['df'], key="editable_dataframe")
        
        # 編集内容をセッションステートに保存
        st.session_state['df'] = edited_df
        
        # 編集後のデータを表示
        st.write("編集後のデータ:")
        st.dataframe(edited_df)
        
        

        # 各列の合計を計算
        calories_sum  = edited_df["熱量(kcal)"].sum()
        protein_sum = edited_df["タンパク質(g)"].sum()
        fat_sum = edited_df["脂質(g)"].sum()
        carbohydrates_sum = edited_df["炭水化物(g)"].sum()


        col1, col2 = st.columns(2)        

        # PFCバランス計算
        PFC_calculation(calories_sum, protein_sum, fat_sum, carbohydrates_sum)

        




        





        
