# HANBAO Marketing Intelligence

A GitHub-ready Streamlit starter for understanding customer and sales data, with a practical segmentation workflow inspired by Mark Ritson's evidence-led marketing approach.

## Included
- Customer profile and transaction CSV uploads
- Flexible column aliases for common guest/POS export fields
- Explainable RFM segments: Loyal regulars, Growing relationship, Lapsed customers, Recent first-timers, One-time/at risk
- Segment size/value summaries and suggested hypotheses/actions
- Customer explorer and CSV exports
- Item/category and occasion analysis when the data contains those fields
- Campaign brief builder with objective, audience, proposition, channels and KPI
- Data quality notes and sample data for trying the app

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to GitHub + Streamlit Community Cloud
1. Create a new GitHub repository.
2. Upload `app.py`, `requirements.txt`, and `README.md`.
3. Commit and push.
4. In Streamlit Community Cloud, create an app from that repository and select `app.py`.
5. Upload your own CSV exports in the app.

## Data format
### Customer profiles CSV
Recommended columns: `customer_id`, `first_name`, `email`, `marketing_opt_in`, `channel`, `occasion`, `party_type`, `visit_motivation`, `price_sensitivity`, `postcode`.

Common aliases such as `guest_id`, `profile_id`, and `email_address` are normalised automatically.

### Transactions / orders CSV
Recommended columns: `customer_id`, `transaction_id`, `date`, `spend_gbp`, `location`, `item`, `category`, `quantity`.

Common aliases such as `order_id`, `order_date`, `amount`, `revenue`, `total`, `product_name`, and `qty` are normalised automatically. If your exports use other names, rename columns before upload.

For Tevalis sales without guest IDs, you can still analyse item/category and overall sales, but customer-level RFM requires a reliable customer ID linked to transactions. SevenRooms guest-linked spend/itemised orders are useful for that connection.

## Important limitations
- Sample records are fictional.
- Segment labels are transparent rules, not machine-learning truth or validated customer needs.
- RFM is a behavioural starting point; a robust needs-based segmentation also requires market/customer research and evidence about needs, attitudes, barriers and choice.
- No live integrations, database persistence, campaign sending, authentication, or automatic marketing consent handling are included.
- Uploaded data is processed in the Streamlit session. Do not upload payment-card data or unnecessary sensitive personal data. Add authentication, secure storage, access controls, retention rules and privacy review before using this for identifiable customer records at scale.
- Check your platform's current data/privacy and deployment settings before uploading real customer information.

## Roadmap
1. Map actual SevenRooms and Tevalis export schemas.
2. Add DuckDB persistence and import validation.
3. Add cohort retention, repeat visit windows and customer lifetime value.
4. Add campaign tracking, control groups and incremental margin.
5. Add needs-based segment profiles from customer research.
6. Add authenticated access and a proper deployment/security setup.
