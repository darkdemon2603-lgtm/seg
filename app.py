import io
from datetime import date
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="HANBAO Marketing Intelligence", page_icon="🍔", layout="wide")

# ---------------- Data helpers ----------------
ALIASES = {
    "customer_id":"customer_id", "guest_id":"customer_id", "profile_id":"customer_id", "id":"customer_id",
    "email":"email", "email_address":"email", "first_name":"first_name", "name":"name",
    "order_id":"transaction_id", "transaction":"transaction_id", "transaction_id":"transaction_id", "booking_id":"transaction_id",
    "date":"date", "order_date":"date", "visit_date":"date", "created_at":"date", "transaction_date":"date",
    "spend":"spend_gbp", "amount":"spend_gbp", "revenue":"spend_gbp", "sales":"spend_gbp", "net_sales_gbp":"spend_gbp",
    "total":"spend_gbp", "total_spend":"spend_gbp", "transaction_value_gbp":"spend_gbp", "spend_gbp":"spend_gbp",
    "item":"item", "product":"item", "product_name":"item", "menu_item":"item",
    "category":"category", "item_category":"category", "quantity":"quantity", "qty":"quantity",
    "channel":"channel", "source":"channel", "location":"location", "venue":"location",
    "occasion":"occasion", "visit_occasion":"occasion", "party_type":"party_type",
    "postcode":"postcode", "postal_code":"postcode", "marketing_opt_in":"marketing_opt_in",
    "birthday_month":"birthday_month", "rating":"rating", "satisfaction":"satisfaction",
    "dietary_preference":"dietary_preference", "price_sensitivity":"price_sensitivity",
    "visit_motivation":"visit_motivation", "customer_type":"customer_type"
}

def clean(df):
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
    return df.rename(columns={c: ALIASES.get(c, c) for c in df.columns})

def read_upload(upload):
    if upload is None: return None
    try:
        return clean(pd.read_csv(upload))
    except Exception as e:
        st.error(f"Could not read {upload.name}: {e}")
        return None

def money(x):
    return "—" if pd.isna(x) else f"£{x:,.2f}"

def sample_data():
    rng=np.random.default_rng(17)
    n=140
    ids=[f"G{i:04d}" for i in range(1,n+1)]
    customers=pd.DataFrame({
        "customer_id":ids,
        "first_name":[f"Guest{i}" for i in range(1,n+1)],
        "marketing_opt_in":rng.choice(["yes","no"],n,p=[.72,.28]),
        "channel":rng.choice(["Instagram","Google","Direct","Word of mouth","Email"],n,p=[.24,.22,.2,.2,.14]),
        "occasion":rng.choice(["Casual meal","Birthday","Date night","Group celebration","Family"],n,p=[.4,.12,.15,.2,.13]),
        "party_type":rng.choice(["Couple","Friends","Family","Solo","Work"],n),
        "visit_motivation":rng.choice(["Treat myself","Social occasion","Convenience","Try something new","Value"],n),
        "price_sensitivity":rng.choice(["Low","Medium","High"],n,p=[.3,.45,.25]),
        "postcode":rng.choice(["WR1","WR2","B1","B2","Other"],n,p=[.28,.24,.15,.12,.21])
    })
    rows=[]
    today=pd.Timestamp.today().normalize()
    for i,cid in enumerate(ids):
        visits=int(rng.choice([1,2,3,4,6,9],p=[.34,.25,.17,.12,.08,.04]))
        base_days=int(rng.integers(5,300))
        for j in range(visits):
            dt=today-pd.Timedelta(days=min(365,base_days+j*int(rng.integers(12,65))))
            spend=round(float(np.clip(rng.normal(28,12),9,105)),2)
            rows.append({"customer_id":cid,"transaction_id":f"T{i:04d}_{j}","date":dt.date().isoformat(),"spend_gbp":spend,
                         "channel":c["channel"],"location":rng.choice(["Worcester","Birmingham"]),"item":rng.choice(["Burger","Fries","Cocktail","Soft drink","Chicken burger","Vegan burger"]),
                         "category":rng.choice(["Burgers","Sides","Drinks","Vegan"]),"quantity":int(rng.integers(1,4))})
    return customers,pd.DataFrame(rows)

def rfm_build(customers, tx):
    if tx is None or tx.empty or "customer_id" not in tx.columns:
        return customers.copy()
    t=tx.copy()
    if "date" not in t: t["date"]=pd.NaT
    t["date"]=pd.to_datetime(t["date"],errors="coerce")
    if "spend_gbp" not in t: t["spend_gbp"]=np.nan
    t["spend_gbp"]=pd.to_numeric(t["spend_gbp"],errors="coerce")
    t=t.dropna(subset=["customer_id"])
    anchor=t["date"].max()
    if pd.isna(anchor): anchor=pd.Timestamp.today().normalize()
    agg=t.groupby("customer_id").agg(
        last_visit=("date","max"),
        frequency=("transaction_id","nunique") if "transaction_id" in t else ("spend_gbp","count"),
        monetary_value=("spend_gbp","sum"),
        average_spend=("spend_gbp","mean"),
        transaction_rows=("spend_gbp","count")
    ).reset_index()
    agg["recency_days"]=(anchor-agg["last_visit"]).dt.days
    agg["frequency"]=agg["frequency"].fillna(0).astype(int)
    agg["monetary_value"]=agg["monetary_value"].fillna(0)
    agg["average_spend"]=agg["average_spend"].fillna(0)
    # Explainable, rules-based labels, not an opaque clustering model.
    def segment(r):
        if r["frequency"] >= 4 and r["recency_days"] <= 60: return "Loyal regulars"
        if r["frequency"] >= 2 and r["recency_days"] <= 90: return "Growing relationship"
        if r["recency_days"] > 120 and r["frequency"] >= 2: return "Lapsed customers"
        if r["frequency"] == 1 and r["recency_days"] <= 60: return "Recent first-timers"
        if r["frequency"] == 1: return "One-time / at risk"
        return "Needs data"
    agg["rfm_segment"]=agg.apply(segment,axis=1)
    if customers is not None and not customers.empty and "customer_id" in customers:
        out=customers.drop_duplicates("customer_id").merge(agg,on="customer_id",how="left")
    else: out=agg
    return out

def csv_download(df):
    return df.to_csv(index=False).encode("utf-8")

# ---------------- UI ----------------
st.title("HANBAO Marketing Intelligence")
st.caption("A practical segmentation and marketing decision platform inspired by Mark Ritson's evidence-led approach.")
st.info("Use segmentation to make choices: who to prioritise, what they need, how to reach them, and what to measure. The sample data is fictional; upload real exports before drawing conclusions.")

with st.sidebar:
    st.header("Data sources")
    customer_upload=st.file_uploader("Customer / guest profiles CSV",type=["csv"])
    tx_upload=st.file_uploader("Orders / transactions CSV",type=["csv"])
    st.caption("Works with exports from SevenRooms and Tevalis after column mapping/cleanup. No live connection is assumed.")
    st.markdown("---")
    st.header("Analysis filters")
    location_filter=st.selectbox("Location",["All locations","Worcester","Birmingham"])
    min_spend=st.number_input("Minimum lifetime spend (£)",min_value=0.0,value=0.0,step=5.0)
    st.caption("Customer data stays in this app session; this starter has no persistent database.")

cu=read_upload(customer_upload); tx=read_upload(tx_upload)
if cu is None and tx is None:
    cu,tx=sample_data()
    st.warning("Showing illustrative sample data. Replace it with your actual data.")
elif cu is None:
    cu=pd.DataFrame()
elif tx is None:
    tx=pd.DataFrame(columns=["customer_id","transaction_id","date","spend_gbp"])

if tx is not None and not tx.empty:
    if "location" in tx and location_filter!="All locations":
        tx=tx[tx["location"].astype(str).str.casefold()==location_filter.casefold()]
customers=rfm_build(cu,tx)
if "monetary_value" in customers:
    customers["monetary_value"]=pd.to_numeric(customers["monetary_value"],errors="coerce").fillna(0)
    customers=customers[customers["monetary_value"]>=min_spend]

tabs=st.tabs(["Executive overview","Segmentation","Customer explorer","Product & occasion","Campaign planner","Data quality & guide"])
with tabs[0]:
    st.subheader("What is happening?")
    a,b,c,d=st.columns(4)
    a.metric("Profiles",f"{customers['customer_id'].nunique():,}" if "customer_id" in customers else "—")
    b.metric("Transaction rows",f"{len(tx):,}")
    c.metric("Recorded sales",money(pd.to_numeric(tx.get("spend_gbp",pd.Series(dtype=float)),errors="coerce").sum()))
    d.metric("Customers with opt-in",f"{(customers['marketing_opt_in'].astype(str).str.lower().isin(['yes','true','1','y'])).mean():.0%}" if "marketing_opt_in" in customers and len(customers) else "—")
    left,right=st.columns(2)
    with left:
        st.markdown("**Customer segments**")
        if "rfm_segment" in customers:
            seg=customers["rfm_segment"].value_counts().rename_axis("Segment").reset_index(name="Customers")
            st.bar_chart(seg.set_index("Segment"))
            st.dataframe(seg,use_container_width=True,hide_index=True)
    with right:
        st.markdown("**Sales by item category**")
        if not tx.empty and {"category","spend_gbp"}.issubset(tx.columns):
            cat=tx.groupby("category",dropna=False)["spend_gbp"].sum().sort_values(ascending=False)
            st.bar_chart(cat)
        else: st.caption("Upload itemised transactions with category and spend_gbp to see category sales.")
    st.markdown("**Read this correctly**")
    st.write("This is descriptive analysis, not proof of causation. Segment labels are transparent rules based on recency, frequency and spend. Validate with commercial knowledge, customer research and campaign tests.")

with tabs[1]:
    st.subheader("Segmentation: from data to choices")
    st.write("Ritson-inspired principle: segment by meaningful differences in needs/behaviour, assess commercial value, then choose which groups to prioritise. Demographics alone rarely explain enough.")
    if "rfm_segment" in customers:
        summary=customers.groupby("rfm_segment",dropna=False).agg(
            Customers=("customer_id","nunique"),
            Avg_lifetime_spend=("monetary_value","mean"),
            Median_lifetime_spend=("monetary_value","median"),
            Avg_visits=("frequency","mean"),
            Avg_days_since_visit=("recency_days","mean")
        ).reset_index().rename(columns={"rfm_segment":"Segment"})
        summary["Share_of_profiles_pct"]=summary["Customers"]/max(1,summary["Customers"].sum())*100
        st.dataframe(summary.style.format({"Avg_lifetime_spend":"£{:,.2f}","Median_lifetime_spend":"£{:,.2f}","Avg_visits":"{:.1f}","Avg_days_since_visit":"{:.0f}","Share_of_profiles_pct":"{:.1f}%"}),use_container_width=True,hide_index=True)
        chosen=st.selectbox("Inspect a segment",summary["Segment"].tolist())
        row=summary[summary["Segment"]==chosen].iloc[0]
        st.markdown(f"### {chosen}")
        st.write(f"**Commercial role:** {int(row['Customers'])} profiles, average recorded lifetime spend {money(row['Avg_lifetime_spend'])}, average {row['Avg_visits']:.1f} visits.")
        playbooks={
          "Loyal regulars":("Protect and reward habit","Early access, loyalty milestones, new menu previews","Repeat rate, incremental spend, reward cost"),
          "Growing relationship":("Build frequency and repertoire","Prompt a second/third visit, suggest complementary menu categories","Repeat within 60 days, category attachment"),
          "Lapsed customers":("Win back selectively","Relevant newness or occasion-led message; suppress if no consent","Reactivation rate, incremental margin, unsubscribe rate"),
          "Recent first-timers":("Turn trial into a habit","Thank-you message, clear next reason to visit, loyalty introduction","Second visit within 45–60 days"),
          "One-time / at risk":("Learn why they did not return","Light-touch feedback, menu/news proof, no blanket discount","Return rate, feedback themes"),
          "Needs data":("Fix identity and transaction linkage","Match customer IDs and transaction records","Profile match rate, missing IDs")
        }
        goal,tactics,measure=playbooks.get(chosen,("Research the group","Interview or survey customers","Test measurable response"))
        st.markdown(f"**Objective:** {goal}")
        st.markdown(f"**Possible actions:** {tactics}")
        st.markdown(f"**Measure:** {measure}")
        st.caption("These are hypotheses to test, not claims about what customers want.")
    st.download_button("Export segmented customer table",csv_download(customers),"hanbao_segmented_customers.csv","text/csv")

with tabs[2]:
    st.subheader("Customer explorer")
    if "customer_id" in customers:
        cols=[c for c in ["customer_id","first_name","name","email","rfm_segment","frequency","recency_days","monetary_value","average_spend","occasion","party_type","visit_motivation","channel","marketing_opt_in","postcode"] if c in customers]
        query=st.text_input("Search ID, name, email, segment or postcode")
        view=customers[cols].copy()
        if query:
            mask=view.astype(str).apply(lambda col:col.str.contains(query,case=False,na=False)).any(axis=1)
            view=view[mask]
        st.dataframe(view,use_container_width=True,hide_index=True)
        st.download_button("Download current customer view",csv_download(view),"hanbao_customer_explorer.csv","text/csv")
    else: st.warning("A customer_id (or guest_id/profile_id) column is needed to link profiles to transactions.")

with tabs[3]:
    st.subheader("Product, occasion and need-state analysis")
    l,r=st.columns(2)
    with l:
        st.markdown("**What sells?**")
        if not tx.empty and "item" in tx:
            item_col="spend_gbp" if "spend_gbp" in tx else "quantity" if "quantity" in tx else None
            if item_col:
                st.bar_chart(tx.groupby("item")[item_col].sum().sort_values(ascending=False).head(15))
                st.dataframe(tx.groupby("item").agg(Rows=("item","size"),Value=(item_col,"sum")).sort_values("Value",ascending=False).head(15),use_container_width=True)
            else: st.caption("Add spend_gbp or quantity to item-level sales.")
        else: st.caption("Upload item-level sales to identify best sellers.")
    with r:
        st.markdown("**Who comes for what?**")
        if "occasion" in customers:
            # Profiles may not have linked transactions, so RFM columns may be absent.
            occasion_data = customers.copy()
            if "customer_id" not in occasion_data.columns:
                occasion_data["customer_id"] = pd.Series(range(len(occasion_data)), index=occasion_data.index)
            if "monetary_value" not in occasion_data.columns:
                occasion_data["monetary_value"] = np.nan
            occasion_summary = (
                occasion_data.groupby("occasion", dropna=False)
                .agg(Customers=("customer_id", "nunique"), Avg_spend=("monetary_value", "mean"))
                .reset_index()
            )
            st.dataframe(occasion_summary, use_container_width=True, hide_index=True)
            if occasion_data["monetary_value"].isna().all():
                st.caption("Average spend is unavailable because customer profiles are not linked to transaction spend. Upload transactions with matching customer IDs and spend values.")
        else:
            st.write("Add survey/profile fields such as occasion, party_type, visit_motivation or dietary_preference. Do not infer motivations from transaction data alone.")
    st.markdown("**Research questions worth answering**")
    st.write("- Which occasions are under-served or under-promoted?\n- What needs drive choice: socialising, convenience, indulgence, novelty or value?\n- Which groups buy across categories, and which only buy a main?\n- What would make a first visit become a repeat visit?")
    st.caption("Needs and attitudes should come from research or explicitly collected data—not be fabricated by an algorithm.")

with tabs[4]:
    st.subheader("Campaign planner")
    st.write("Build a testable brief for one segment. The planner does not send messages; it helps define the strategy and measurement.")
    segs=customers["rfm_segment"].dropna().unique().tolist() if "rfm_segment" in customers else ["All customers"]
    with st.form("campaign"):
        objective=st.selectbox("Business objective",["Increase repeat visits","Reactivate lapsed guests","Grow average spend","Promote a menu launch","Increase weekday demand","Grow opted-in database"])
        target=st.selectbox("Target segment",segs+["All opted-in customers"])
        insight=st.text_area("Evidence / customer insight",placeholder="What do we know from sales, bookings, interviews or survey data?")
        proposition=st.text_input("Proposition",placeholder="Why should this audience choose HANBAO now?")
        channel=st.multiselect("Channel",["Email","SMS","Instagram","Paid social","Website","In-venue","Partner"])
        offer=st.text_input("Offer / experience (optional)",placeholder="Prefer value/experience first; use discount only if justified")
        kpi=st.selectbox("Primary KPI",["Incremental gross profit","Repeat visit rate","Redemption / response rate","Average spend per cover","Qualified email opt-ins","Revenue vs control group"])
        period=st.selectbox("Measurement window",["14 days","30 days","45 days","60 days","90 days"])
        submitted=st.form_submit_button("Generate campaign brief")
    if submitted:
        st.markdown("### Campaign brief")
        st.markdown(f"**Objective:** {objective}\n\n**Target:** {target}\n\n**Evidence:** {insight or 'Evidence needed before launch.'}\n\n**Proposition:** {proposition or 'Define a clear customer reason to act.'}\n\n**Channels:** {', '.join(channel) if channel else 'Choose based on audience reach and consent.'}\n\n**Offer/experience:** {offer or 'No discount specified.'}\n\n**Primary KPI:** {kpi}\n\n**Window:** {period}")
        st.markdown("**Before launch:** define a baseline, select a holdout/control where feasible, confirm marketing consent, calculate expected margin, and set a stop/scale rule.")
        st.download_button("Download campaign brief",f"HANBAO CAMPAIGN BRIEF\n\nObjective: {objective}\nTarget: {target}\nEvidence: {insight}\nProposition: {proposition}\nChannels: {', '.join(channel)}\nOffer: {offer}\nKPI: {kpi}\nWindow: {period}\n".encode(),"hanbao_campaign_brief.txt","text/plain")

with tabs[5]:
    st.subheader("Data quality and how to use this")
    st.markdown("### Minimum useful exports")
    st.markdown("- **Customer / SevenRooms:** customer_id or guest_id, marketing_opt_in, plus any consented profile fields.\n- **Tevalis / orders:** transaction_id, date, spend_gbp, customer_id where available, item/category/quantity if itemised.\n- **Optional research:** occasion, visit motivation, party type, price sensitivity, satisfaction. These need to be asked/collected—not guessed.")
    checks=[]
    for label,df,required in [("Customer profiles",cu,["customer_id"]),("Transactions",tx,["date","spend_gbp"])]:
        missing=[x for x in required if x not in df.columns]
        checks.append({"Dataset":label,"Rows":len(df),"Missing recommended fields":", ".join(missing) if missing else "None"})
    st.dataframe(pd.DataFrame(checks),use_container_width=True,hide_index=True)
    if "customer_id" in tx and len(tx):
        st.metric("Transactions linked to customer ID",f"{tx['customer_id'].notna().mean():.1%}")
    st.markdown("### Method and caveats")
    st.markdown("- **Descriptive, explainable RFM:** recency, frequency and monetary value are starting signals, not a full needs-based segmentation.\n- **Mark Ritson-inspired workflow:** diagnose the market/customer, identify meaningful segments, assess size/value/reachability, choose target segments, define positioning/proposition, activate, measure and refine.\n- **No automatic causal claims:** compare campaigns with baseline/control groups where possible.\n- **Privacy:** use only data you are authorised to process; minimise personal fields, honour consent and suppression lists, and do not upload payment-card data or unnecessary sensitive information.\n- **Production gap:** this version uses session uploads and sample data. It does not persist records, send campaigns, or connect directly to SevenRooms/Tevalis.")
    st.markdown("### Suggested next build")
    st.write("1. Validate actual export schemas. 2. Add DuckDB persistence and import history. 3. Add cohort/retention and campaign-control reporting. 4. Add research-based needs segmentation. 5. Add authentication and role-based access before storing identifiable customer data.")
