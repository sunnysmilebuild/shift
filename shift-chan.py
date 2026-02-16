import streamlit as st
import pandas as pd

# 1. ページ設定とデザイン（CSS）
st.set_page_config(page_title="シフトちゃん", page_icon="📅", layout="wide")

def apply_custom_design():
    """外見CSS"""
    st.markdown(
        """
        <style>
        /* タイトルボックス全体のデザイン */
        .title-container {
            text-align: center; 
            color: #d63384; 
            background-color: #fff0f6; 
            padding: 20px; 
            border-radius: 15px; 
            border: 2px solid #ffc1e3; 
            margin-bottom: 30px;
            font-size: 1.8rem; /* PCでの文字サイズ */
            font-weight: bold;
            line-height: 1.3;
        }

        /* PCでは改行を隠す */
        .mobile-br {
            display: none;
        }

        /* スマホ（幅640px以下）の設定 */
        @media (max-width: 640px) {
            .title-container {
                font-size: 1.4rem; /* スマホでは少し小さく */
                padding: 15px;
            }
            /* スマホの時だけ改行を有効にする */
            .mobile-br {
                display: inline;
            }
        }
        /* メイン背景とサイドバーの背景色 */
        [data-testid="stSidebar"] {
            background-color: #fff0f6; /* 薄いピンク */
        }
        
        /*通常のstButton【ピンクボタン】(secondary: デフォルト) */
        div.stButton > button[kind="secondary"] {
            background-color: #ff85c0 !important;
            color: white !important;
            border-radius: 20px !important;
            border: none !important;
            padding: 10px 20px !important;
            font-weight: bold !important;
        }

        /*  戻るボタン（primary） */
        div.stButton > button[kind="primary"] {
            background-color: #fff0f6 !important; /* ごく薄いピンク（背景） */
            color: #d63384 !important;           /* 濃いピンク（文字） */
            border-radius: 20px !important;
            border: 2px solid #ff85c0 !important; /* ピンクの枠線 */
            padding: 10px 20px !important;
            font-weight: bold !important;
            width: 100% !important;
        }

        /* 通常のstButton */
        div.stButton > button[kind="secondary"]:hover {
            background-color: #f759ab !important;
        }
        /* 戻るボタンのホバー（マウスを乗せた時） */
        div.stButton > button[kind="primary"]:hover {
            background-color: #ffd6e7 !important; /* ホバー時は少しだけ濃く */
            border-color: #f759ab !important;     /* 枠線も少し濃く */
            color: #f759ab !important;
        }
        /* ダウンロードボタン */
        div.stDownloadButton > button {
            background-color: #ff85c0;
            color: white;
            border-radius: 20px;
            width: 100%;
        }
        
        /* ラジオボタンや数値入力のラベルを少し太字に */
        .stMarkdown, label {
            color: #d63384;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

######## 関数定義（ロジック系） ########
# アップロードファイルフォーマットチェック
def validate_csv_format(uploaded_file):

    try:
        # 1. Excel対応（エンコーディング対応）
        # まず標準のutf-8で試し、失敗したらExcel(Windows)標準のcp932で読み直す
        try:
            df_original = pd.read_csv(uploaded_file, header=None)
        except UnicodeDecodeError:
            uploaded_file.seek(0)# ファイルポインタを先頭に戻す
            df_original = pd.read_csv(uploaded_file, header=None, encoding='cp932')
        
        # 2. サイズチェック（ご自身で追加された正解のバリデーション）
        # ヘッダー4行、データ1行以上の計5行、および最低3列が必要
        if df_original.shape[0] < 5 or df_original.shape[1] < 3:
            st.error("⚠️ ファイルの形式が正しくありません。")
            st.warning("正しいフォーマットのCSVファイル（テンプレート）を使用してください。")
            st.stop()
            
        return df_original
        
    except Exception as e:
        # CSV以外のファイル（画像やPDF等）が投げ込まれた場合の最終防衛線
        st.error(f"❌ ファイルの読み込み中にエラーが発生しました。")
        st.info("CSVファイルであることを確認してください。")
        st.stop()

def highlight_area(data):
    # 1. 土台となる空のスタイル表
    styles = pd.DataFrame("", index=data.index, columns=data.columns)
    
    # 2. セルの内容に応じた色分け（データ部分）
    for r in range(len(data)):
        for c in range(len(data.columns)):
            val = str(data.iloc[r, c])
            
            if '◎' in val:
                # 薄めの黄色
                styles.iloc[r, c] = "background-color: #fff9c4; color: #5d4037; font-weight: bold;"
            elif '▲' in val:
                # 優しめのオレンジ（▲が際立つ）
                styles.iloc[r, c] = "background-color: #ffe0b2; color: #5d4037; font-weight: bold;"
                
    # 3. ヘッダーと名前列のピンク枠（上書きで優先）
    # 背景色を少しだけ透過させない濃さに調整
    pink_style = "background-color: #ffd6e7; color: #5d4037; font-weight: bold;"
    styles.iloc[0:4, :] = pink_style
    styles.iloc[:, 0:2] = pink_style
    
    return styles


#1行目の日付の正規化
def normalize_dates(date_series):
    normalized_series = date_series.str.translate(
        str.maketrans("０１２３４５６７８９／－", "0123456789/-")
    )
    dummy_year = pd.Timestamp.today().year
    normalized_series = (
        normalized_series.astype(str).str.strip()
        .str.replace("年", "/", regex=False)
        .str.replace("月", "/", regex=False)
        .str.replace("日", "", regex=False)
        .str.replace("-", "/", regex=False)
        .str.replace(r"\s+", "", regex=True)
        .apply(lambda x: f"{dummy_year}/{x}" if pd.notna(x) and x.count("/") == 1 else x)
        .pipe(pd.to_datetime, errors="coerce")
        .dt.strftime("%Y/%m/%d")
    )
    return normalized_series

#df_workを調整
def adjust_dfwork(df_work, radio, required_staff): 
    row1 = normalize_dates(df_work.iloc[0, 2:])
    df_work.iloc[0,2:] = row1 
    df_work.iloc[4:,1] = pd.to_numeric(df_work.iloc[4:, 1], errors='coerce').fillna(0)

    #work列3列追加
    df_work['dates'] = [[] for _ in range(len(df_work))]
    df_work["kaisu"] = 0 
    df_work["penalty_score"] = pd.to_numeric(df_work.iloc[:, 1], errors='coerce').fillna(0)

    #work行3行追加
    target_area = df_work.iloc[4:, 2:-3]
    toban_sum = pd.Series(0, index=df_work.columns, name="ninzu")
    maru_sum = (target_area == "〇").sum().reindex(df_work.columns, fill_value=0).rename("maru_sum")
    sankaku_sum = (target_area == "△").sum().reindex(df_work.columns, fill_value=0).rename("sankaku_sum")
    col_index = pd.Series(range(len(df_work.columns)), index=df_work.columns, name="original_column")
    
    df_work = pd.concat([df_work, toban_sum.to_frame().T, maru_sum.to_frame().T, sankaku_sum.to_frame().T, col_index.to_frame().T])

    #指定人数に満たない場合は日付項目をNoneに変更→割り当て対象外
    if radio == "練習中止": 
        total_available = maru_sum + sankaku_sum
        is_understaffed = total_available < required_staff
        df_work.loc[df_work.index[0], is_understaffed] = None

    #〇の数の少ない列からソートしなおし
    fixed_cols = df_work.iloc[:,:2]
    sort_cols = df_work.iloc[:,2:-3].sort_values(by="maru_sum", axis=1)
    fixed_cols2 = df_work.iloc[:,-3:]
    df_work = pd.concat([fixed_cols, sort_cols, fixed_cols2], axis=1)
    
    return df_work, row1 

#当番が決まったあとの処理    
def toban(df, row, col, kigou):
    df.at[row, col] = kigou
    df.at[row, 1] = int(df.at[row, 1]) + 1 
    df.at[row, "kaisu"] += 1 
    df.at[row, "dates"].append(df.at[0, col])

#当番割り当て処理
def assign(df_work, col, rows, required_staff, date_list, kigou):
    df_work.loc[4:, "penalty_score"] = df_work.loc[4:, 1]
    target_date = df_work.at[df_work.index[0], col]
    idx_position = date_list.to_list().index(target_date) 
    mae_date = date_list.iloc[idx_position - 1] if idx_position > 0 else None
    ato_date = date_list.iloc[idx_position + 1] if idx_position < len(date_list) - 1 else None

    #同日、前後日でペナルティスコア増加
    for row in rows:
        t_dates = df_work.at[row, "dates"]
        if t_dates:
            if target_date in t_dates: df_work.at[row,"penalty_score"] += 5
            if mae_date in t_dates: df_work.at[row,"penalty_score"] += 1
            if ato_date in t_dates: df_work.at[row,"penalty_score"] += 1
    
    sorted_rows = sorted(rows, key=lambda r: (df_work.at[r, "penalty_score"], df_work.iloc[r, 2:-3].eq("〇").sum()))
    selected_rows = sorted_rows[:required_staff]
    for row in selected_rows:
        toban(df_work, row, col, kigou)

#〇の人の割り当て
def assign_maru(df_work, row1, required_staff, date_list):
    for col in df_work.columns[2:]:  
        maru_rows = df_work[(df_work[col] == "〇")].index
        if pd.notna(df_work.at[df_work.index[0], col]):
            if df_work.at["maru_sum",col] > required_staff:
                assign(df_work, col, maru_rows, required_staff, date_list,"◎")
            else:
                for row in maru_rows: toban(df_work, row, col, "◎")
    return df_work, row1, required_staff

#△の人の割り当て    
def assign_sankaku(df_work, required_staff, date_list):
    df_work.loc["ninzu",df_work.columns[2:-3]] = (df_work.iloc[4:, 2:-3] == "◎").sum()
    short_cols = [col for col in df_work.columns[2:-3] if df_work.at["ninzu", col] < required_staff]
    if short_cols:
        for col2 in short_cols:
            if pd.notna(df_work.at[df_work.index[0], col2]):
                sankaku_rows = df_work[(df_work[col2] == "△")].index
                fusoku = required_staff - df_work.at["ninzu", col2]
                if df_work.at["sankaku_sum",col2] > fusoku:
                    assign(df_work, col2, sankaku_rows, fusoku, date_list, "▲")
                else:
                    for row in sankaku_rows: toban(df_work, row, col2, "▲") 
    return df_work, required_staff

#集計行    
def shukei(df_work):
    data_area = df_work.iloc[4:-4, 2:-3]
    df_work.loc["ninzu", df_work.columns[2:-3]] = data_area.isin(["◎", "▲"]).sum()
    df_work.loc["maru_sum", df_work.columns[2:-3]] = (data_area == "◎").sum()
    df_work.loc["sankaku_sum", df_work.columns[2:-3]] = (data_area == "▲").sum()

    # --- 集計行の不要な「0」を消す処理 ---
    # 2列目(累積)、最終3列(当番日付、回数、スコア)の集計行を空にする
    shukei_rows = ["ninzu", "maru_sum", "sankaku_sum"]
    df_work.loc[shukei_rows, df_work.columns[1]] = ""  # 2列目の0を消す
    df_work.loc[shukei_rows, df_work.columns[-3:]] = "" # 右端3列の0を消す
    
    fixed_cols = df_work.iloc[:,:2]
    sort_cols = df_work.iloc[:,2:-3].sort_values(by="original_column", axis=1)
    fixed_cols2 = df_work.iloc[:,-3:]
    return pd.concat([fixed_cols, sort_cols, fixed_cols2], axis=1)

#結果表示用データ作成
def copy_to_original(df_work, df_original):
    #df_originalに集計列2列追加
    df_original["toban_bi"] = None
    df_original["kaisu"] = None

    #df_originalに集計行3行追加
    extra_rows = pd.DataFrame(None, index=range(3), columns=df_original.columns)
    df_original = pd.concat([df_original, extra_rows], ignore_index=True)

    # dates列の中身（日付リスト）をソートしてからCSV用の文字列にする
    #df_work["dates"] = df_work["dates"].apply(
    #    lambda x: ", ".join(sorted([d for d in x if d])) if isinstance(x, list) else x
    #)
    df_work["dates"] = df_work["dates"].apply(
        lambda x: " " + ", ".join(sorted([d for d in x if d])) if (isinstance(x, list) and x) else x
    )
    #当番日欄の西暦削除
    df_work["dates"] = df_work["dates"].str.replace(r"\d{4}/", "", regex=True)
    # 月と日の先頭にある「0」を削除する「01/01」→「1/1」
    df_work["dates"] = df_work["dates"].str.replace(r"\b0+(\d)", r"\1", regex=True)
    
    #df_workを5行目から、最後の一行(original_column)の直前まで抜き出す
    data_start = 4
    target_data = df_work.iloc[data_start:-1, :-1]
    df_original.iloc[data_start : data_start + len(target_data), :target_data.shape[1]] = target_data.to_numpy()
    df_original.iloc[0,-2:] = ["当番日","今回当番回数"]
    df_original.iloc[-3:, 0] = ["当番人数", "〇当番", "△当番"]
    return df_work, df_original

#配布用データ作成    
def copy_to_haifu(df_original, row1):
    df_haifu = df_original.copy()
    date_col_indices = [i for i, val in enumerate(row1) if pd.notna(val)]
    target_cols = [i + 2 for i in date_col_indices]
    data_start = 4
    for col_idx in target_cols:
        target_area = df_haifu.iloc[data_start:-3,col_idx]
        df_haifu.iloc[data_start:-3, col_idx] = target_area.where(target_area.isin(["◎", "▲"]), "")
    
    cols_to_drop = [df_haifu.columns[1], df_haifu.columns[-1]]
    df_haifu = df_haifu.drop(columns=cols_to_drop)
    summary_col = df_haifu.pop(df_haifu.columns[-1])
    df_haifu.insert(1, summary_col.name, summary_col)
    return df_haifu

######## 画面表示系 関数 ########

def show_sidebar():
    """サイドバーの表示を管理する関数"""
    st.sidebar.markdown("### 🌸 メニュー")
    st.sidebar.markdown("### 1. サンプルCSV")
    #st.sidebar.markdown("### 1.サンプルcsvをダウンロード")
    try:
        with open("data/shift_sample.csv", "rb") as f:
            st.sidebar.download_button(
                label="サンプルダウンロード",
                data=f,
                file_name="shift_sample.csv",
                mime="text/csv"
            )
    except FileNotFoundError:
        st.sidebar.warning("サンプルファイルが見つかりません。")

    st.sidebar.divider()
    st.sidebar.markdown("### 2.スケジュール表のアップロード")
    uploaded_file = st.sidebar.file_uploader("CSVファイルを選択", type="csv")
    return uploaded_file

def show_main_header():
    st.markdown(
        f"""
        <div class="title-container">
            ✨ らくらく当番作成<br class="mobile-br">「シフトちゃん」 ✨
        </div>
        """,
        unsafe_allow_html=True
    )

def show_initial_screen():
    """ファイル未アップロード時の初期画面"""
    st.markdown("""
    ### 🌸 使い方
    ※サイドバーが見えない場合は左上の 》をクリック
    1. サイドバーからサンプルデータをダウンロード
    2. 1の表を編集 (入力方法はこの画面の下参照)
    3. CSV保存 (ExcelはCSV UTR-8(コンマ区切り)がおすすめ)
    4. サイドバーから3のCSVファイルをアップロード
    """)

    try:
        st.write("【サンプルデータ】")
        df_sample = pd.read_csv("data/shift_sample.csv", header=None)
        st.dataframe(df_sample.style.apply(highlight_area, axis=None))
        
    except:
        st.info("サンプルデータなし。管理者に連絡してください。")

    st.markdown("""  
    
    **【入力ルール】**  
    - 1行目：日付（3/23、2026-3-23 など）  
    - 2～4行目：自由項目（曜日、時間、メモなど）  
    - 5行目～：メンバーデータ  
    　（名前、累積回数、〇、△、✕ 、備考）   
       ※累積回数を考慮したくない場合は0で入力
    

    **【割り当てルール（優先順位）】**  
    - 〇から割り当て
    - 足りなかったら△で割り当て
    - 累積回数が少ない人から割り当て  
    - 参加可能日が少ない人から割り当て  
    ※※※※※※※※※※※※
    - 同日の違う時間帯にはなるべく割り当てない    
    - 前後の練習日にもなるべく割り当てない

 
    """)

def show_result_screen(df_original):
    """ファイルアップロード後の処理・結果表示"""
    if not st.session_state.shift_clicked:
        col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 3, 3])
        with col2:
            required_staff = st.number_input("１回あたり当番人数", min_value=1, value=3, step=1)
        with col4:
            radio_val = st.radio('人数不足時', ("練習中止", "練習強行"))
        with col5:
            st.write("")
            if st.button("シフト作成実行", type="secondary"):
                st.session_state.required_staff = required_staff
                st.session_state.radio_selection = radio_val
                st.session_state.shift_clicked = True
                st.rerun()
        st.markdown("""  
    **【割り当てルール（優先順位）】**  
    - 〇から割り当て
    - 足りなかったら△で割り当て 
    - 累積回数が少ない人から割り当て  
    - 参加可能日が少ない人から割り当て  
    ※※※※※※※※※※※※
    - 同日の違う時間帯にはなるべく割り当てない    
    - 前後の練習日にもなるべく割り当てない

 
    """)
        st.write("【アップロードデータ】")
        st.dataframe(df_original.style.apply(highlight_area, axis=None))
    else:
        # シフト作成ロジック
        radio = st.session_state.radio_selection
        required_staff = st.session_state.required_staff
        
        df_work = df_original.copy()
        df_work, row1 = adjust_dfwork(df_work, radio, required_staff)
        date_list = (row1.dropna().drop_duplicates().sort_values())
        df_work, row1, _ = assign_maru(df_work, row1, required_staff, date_list)
        df_work, _ = assign_sankaku(df_work, required_staff, date_list)
        df_work = shukei(df_work)
        df_work, df_original = copy_to_original(df_work, df_original)
        df_haifu = copy_to_haifu(df_original, row1)

        # ダウンロードエリア
        st.markdown("### 📥 割当結果")
        c1, c2, c3, c4 = st.columns([1 ,3 , 3 ,3])
        with c2:
            st.download_button("管理者用ダウンロード", data=df_original.to_csv(index=False, header=False).encode('utf_8_sig'), file_name="shift_result.csv")
        with c3:
            st.download_button("配布用ダウンロード", data=df_haifu.to_csv(index=False, header=False).encode('utf_8_sig'), file_name="shift_haifu.csv")
        with c4:
            if st.button("⬅️ 設定に戻る", type="primary"):
                st.session_state.shift_clicked = False
                st.rerun()
        
        st.divider()
        st.write("【管理者用データ】")
        st.dataframe(df_original.style.apply(highlight_area, axis=None))

        st.write("【配布用データ】")
        st.dataframe(df_haifu.style.apply(highlight_area, axis=None))

######## メイン処理の流れ ########

def main():
    apply_custom_design()
    show_main_header()

    # セッション状態の初期化
    if "shift_clicked" not in st.session_state:
        st.session_state.shift_clicked = False

    # サイドバーの表示
    uploaded_file = show_sidebar()

    # メインコンテンツの分岐
    if uploaded_file is not None:
        df_original = validate_csv_format(uploaded_file)
        show_result_screen(df_original)
    else:
        show_initial_screen()

if __name__ == "__main__":
    main()
