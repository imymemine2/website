import streamlit as st
import pandas as pd
import random
import folium
from streamlit_folium import folium_static
import os

# --- 3. Streamlit アプリの見た目と操作部分 (設定部分は一番最初に) ---
# Webページのタイトルとアイコンを設定します。
# set_page_config() はスクリプトの一番最初のStreamlitコマンドである必要があります。
st.set_page_config(
    page_title="射水「今日どこ行く？」AIコンシェルジュ",
    page_icon="✨",
    layout="wide" # 画面を広く使います。
)

# --- 1. データの読み込み ---
# この @st.cache_data は、一度データを読み込んだら次回からは速く表示できるようにするおまじないです。
@st.cache_data
def load_data():
    try:
        # CSVファイルの名前を 'kosugi.csv' に指定します。
        df = pd.read_csv('kosugi.csv')
        return df
    except FileNotFoundError:
        st.error("エラー: 'kosugi.csv' ファイルが見つかりません。ファイルがアプリと同じディレクトリにあるか確認してください。")
        st.stop() # データが読み込めない場合はアプリを停止します
    except Exception as e:
        st.error(f"データの読み込み中に予期せぬエラーが発生しました: {e}")
        st.stop()

# アプリが起動したら、まずデータを読み込みます。
# アプリ起動時に一度だけデータをロードします
df_spots = load_data()


# --- 2. スポットを提案する仕組み ---
# あなたの選んだ条件に合わせて、おすすめのスポットを選びます。
def recommend_spots(df, mood_input, duration_input, who_with_input):
    filtered_df = df.copy()

    # 「どんな気分？」で選んだものに合わせて絞り込みます。
    # もし「こだわらない」を選んだら、この条件では絞り込みません。
    if mood_input and mood_input != "こだわらない":
        # 'mood'列がNaNでないことを確認し、含まれるかチェック
        filtered_df = filtered_df[filtered_df['mood'].fillna('').str.contains(mood_input, na=False)]

    # 「滞在時間は？」で選んだものに合わせて絞り込みます。
    if duration_input and duration_input != "こだわらない":
        if duration_input == "1時間以内":
            # duration_minが数値であり、かつ60以下であるものをフィルタリング
            filtered_df = filtered_df[pd.notna(filtered_df['duration_min']) & (filtered_df['duration_min'] <= 60)]
        elif duration_input == "2時間以内":
            # duration_minが数値であり、かつ120以下であるものをフィルタリング
            filtered_df = filtered_df[pd.notna(filtered_df['duration_min']) & (filtered_df['duration_min'] <= 120)]
        elif duration_input == "半日（約4時間）":
            # duration_minが数値であり、かつ240以下であるものをフィルタリング
            filtered_df = filtered_df[pd.notna(filtered_df['duration_min']) & (filtered_df['duration_min'] <= 240)]
        elif duration_input == "一日（4時間以上）":
            # 一日過ごすなら、4時間（240分）以上の場所を対象にします。
            # duration_minが数値であり、かつ240以上であるものをフィルタリング
            filtered_df = filtered_df[pd.notna(filtered_df['duration_min']) & (filtered_df['duration_min'] >= 240)]

    # 「誰と行く？」で選んだものに合わせて絞り込みます。
    if who_with_input and who_with_input != "こだわらない":
        # 'who_with'列がNaNでないことを確認し、含まれるかチェック
        filtered_df = filtered_df[filtered_df['who_with'].fillna('').str.contains(who_with_input, na=False)]

    # 提案できるスポットがたくさんある場合、毎回違うおすすめが見つかるように最大3つをランダムに選びます。
    if len(filtered_df) > 3:
        return filtered_df.sample(n=3, random_state=random.randint(0, 1000))
    return filtered_df


# アプリのタイトルと説明文を表示します。
st.title("✨ 射水「今日どこ行く？」AIコンシェルジュ")
st.write("あなたの今日の気分に合わせて、富山県射水市のおすすめスポットをご提案します！")

# --- あなたからの入力部分 ---
st.header("今日の気分を教えてください")

# 入力欄を3つの列に分けて表示します。
col1, col2, col3 = st.columns(3)

with col1:
    # 気分を選ぶドロップダウンメニューです。
    mood_options = ["こだわらない", "のんびり", "美味しいもの", "買い物", "散策", "景色", "体を動かす", "アクティブ", "歴史", "文化"]
    selected_mood = st.selectbox("どんな気分？", mood_options)

with col2:
    # 滞在時間を選ぶドロップダウンメニューです。
    duration_options = ["こだわらない", "1時間以内", "2時間以内", "半日（約4時間）", "一日（4時間以上）"]
    selected_duration = st.selectbox("滞在時間は？", duration_options)

with col3:
    # 誰と行くかを選ぶドロップダウンメニューです。
    who_with_options = ["こだわらない", "一人で", "家族と", "友人と", "カップルで"]
    selected_who_with = st.selectbox("誰と行く？", who_with_options)

# 「おすすめスポットを提案！」ボタンが押されたら、以下の処理が動きます。
if st.button("おすすめスポットを提案！"):
    st.subheader("あなたへのおすすめスポット！")

    # ここで改めてデータをロードし、df_spotsが確実に定義されていることを保証します。
    # @st.cache_dataがあるため、実際のCSV読み込みは初回のみで、2回目以降はキャッシュから高速に取得されます。
    df_spots = load_data() # ★この行が追加・修正された点です★

    # あなたの選んだ条件に合わせて、スポットを提案してもらいます。
    recommended_df = recommend_spots(df_spots, selected_mood, selected_duration, selected_who_with)

    # もし提案されたスポットがあったら、その情報を表示します。
    if not recommended_df.empty:
        # おすすめされたスポットの平均緯度・経度を計算し、地図の中心に設定します。
        # 緯度・経度情報がない場合は、小杉町のデフォルト中心座標を使用します。
        valid_lat = recommended_df['lat'].dropna()
        valid_lon = recommended_df['lon'].dropna()

        if not valid_lat.empty and not valid_lon.empty:
            avg_lat = valid_lat.mean()
            avg_lon = valid_lon.mean()
        else:
            # 緯度・経度情報が全くない場合は、小杉町の中心付近のデフォルト座標を設定
            avg_lat = 36.75
            avg_lon = 137.10
        
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)

        # 提案された各スポットについて、詳しく表示し、地図に印（マーカー）をつけます。
        for index, row in recommended_df.iterrows():
            st.write(f"### {row['name']}") # スポットの名前
            st.write(f"**カテゴリ**: {row['category']}") # カテゴリ
            st.write(f"**おすすめポイント**: {row['description']}") # おすすめポイント
            st.write(f"**住所**: {row['address']}") # 住所

            # ウェブサイトのURLがあればリンクを表示します。
            if pd.notna(row['url']) and row['url'] != '':
                st.markdown(f"[詳しくはこちら]({row['url']})", unsafe_allow_html=True)

            # 画像ファイルがあれば表示します。ファイルが見つからない場合は注意を促します。
            # os.path.exists()はファイルの存在チェックに使う
            if pd.notna(row['image_path']) and row['image_path'] != '' and os.path.exists(row['image_path']):
                st.image(row['image_path'], caption=row['name'], width=300)
            elif pd.notna(row['image_path']) and row['image_path'] != '' and not os.path.exists(row['image_path']):
                st.warning(f"画像ファイルが見つかりません: {row['image_path']}")

            # 地図にスポットの場所を示すマーカー（ピン）を追加します。
            if pd.notna(row['lat']) and pd.notna(row['lon']):
                folium.Marker(
                    [row['lat'], row['lon']],
                    popup=row['name'], # マーカーをクリックしたときに出る名前
                    tooltip=row['name'] # マーカーにカーソルを合わせたときに出る名前
                ).add_to(m)

            st.markdown("---") # スポットごとに区切り線を表示します。

        # 提案されたスポットの地図を表示します。
        st.subheader("おすすめスポットの地図")
        folium_static(m) # Streamlitでfoliumの地図を表示する特別な命令です。

    else:
        # もし、あなたの条件に合うスポットが見つからなかった場合のメッセージです。
        st.info("ご希望に沿うスポットが見つかりませんでした。条件を変えて再度お試しください！")

# アプリの最後に、ちょっとしたメッセージを表示します。
st.markdown("""
---
Created with ❤️ for Imizu, Toyama
""")
