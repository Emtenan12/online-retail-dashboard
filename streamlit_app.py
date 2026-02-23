import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout='wide', page_title='Online Retail Analytics', page_icon='🛍️')

st.markdown('''
<style>
    .stApp { background-color: #1a1f2e; }
    .stApp > header { display: none !important; }
    div[data-testid="stAppViewBlockContainer"] { padding-top: 1rem !important; }
    section[data-testid="stSidebar"] > div { padding-top: 1rem !important; }
    /* FIX: white text everywhere — no gray */
    html, body, [class*="css"], p, li, span, div { color: #f0f4f8 !important; }
    h1, h2, h3, h4 { color: #ffffff !important; }
    h2 { border-bottom: 2px solid #4a5568; padding-bottom: 6px; margin-top: 1.5rem !important; }
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #2d3748 0%, #3a4a6b 100%);
        border: 1px solid #63b3ed; border-radius: 10px; padding: 0.8rem 1.2rem !important;
    }
    [data-testid="metric-container"] label { color: #bee3f8 !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 1px; }
    [data-testid="metric-container"] [data-testid="metric-value"] { color: #ffffff !important; font-size: 1.6rem !important; font-weight: 700; }
    [data-testid="stSidebar"] { background-color: #1e2535 !important; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    .stTabs [data-baseweb="tab"] { color: #bee3f8 !important; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #ffffff !important; border-bottom-color: #63b3ed !important; }
    .stDataFrame, .stDataFrame * { color: #1a202c !important; }
    .stRadio label, .stRadio span { color: #e2e8f0 !important; }
    .insight-box { background: #2a4a6b; border-left: 4px solid #63b3ed; border-radius: 8px; padding: 0.9rem 1rem; margin: 0.5rem 0; color: #ffffff; font-size: 0.88rem; }
    .finding    { background: #1a3a26; border-left: 4px solid #48bb78; border-radius: 8px; padding: 0.9rem 1rem; margin: 0.5rem 0; color: #ffffff; font-size: 0.88rem; }
    .warning    { background: #4a2f0a; border-left: 4px solid #ed8936; border-radius: 8px; padding: 0.7rem 1rem; margin: 0.5rem 0; color: #ffffff; font-size: 0.85rem; }
    .recommend  { background: #2d3748; border-left: 4px solid #b794f4; border-radius: 8px; padding: 0.9rem 1rem; margin: 0.5rem 0; color: #ffffff; font-size: 0.88rem; }
</style>
''', unsafe_allow_html=True)

CHART_THEME = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(45,55,72,0.4)',
    font_color='#ffffff',
    title_font_color='#ffffff',
    legend_font_color='#ffffff',
)
AXIS_STYLE = dict(gridcolor='#2d3748', linecolor='#4a5568', tickcolor='#e2e8f0', tickfont_color='#ffffff')

def apply_theme(fig, categoryorder_y=None):
    fig.update_layout(**CHART_THEME)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE, **(dict(categoryorder=categoryorder_y) if categoryorder_y else {}))
    return fig

@st.cache_data
def load_data():
    df = pd.read_parquet('online_retail_customers.parquet')
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['InvoiceMonth'] = pd.to_datetime(df['InvoiceMonth'])
    rfm = pd.read_csv('online_retail_rfm.csv')
    cr  = pd.read_csv('online_retail_customer_returns.csv')
    op  = pd.read_csv('online_retail_op_losses.csv')
    tp  = pd.read_csv('online_retail_top_products.csv')
    sd  = pd.read_csv('online_retail_segment_definitions.csv')
    df['InvoiceYear'] = df['InvoiceDate'].dt.year.astype(int)

  
    EXCLUDE = {'manual','dotcom postage','postage','bank charges','samples','discount'}
    cr = cr[~cr['Description'].str.strip().str.lower().isin(EXCLUDE)].copy()

  
    op['Description'] = op['Description'].str.strip().str.lower().str.replace(r'\s+', ' ', regex=True)
    category_map = {
        'printing smudges/thrown away': 'Printing Issues',
        'damages':              'Damaged Stock',
        'damaged':              'Damaged Stock',
        'wet damages':          'Storage Conditions',
        'damages wax':          'Damaged Stock',
        'mouldy, thrown away.': 'Storage Conditions',
        'thrown away':          'Disposed / Unsaleable',
        'check':                'Uncategorised — needs review',
        'found':                'Uncategorised — needs review',
        'lost':                 'Uncategorised — needs review',
        'samples':              'Samples / Write-offs',
    }
    op['Category'] = op['Description'].map(category_map).fillna('Other')
    return df, rfm, cr, op, tp, sd

df, rfm, customer_returns, op_losses, top_products, seg_defs = load_data()

with st.sidebar:
    st.markdown('## 🛍️ Online Retail')
    st.markdown('**Analytics Dashboard**')
    st.markdown('---')
    page = st.radio('Navigate', [
        '📊 Overview', '👥 Customer Segments',
        '🔄 Cohort Retention', '↩️ Returns Analysis', '🌍 Country Performance'
    ])
    st.markdown('---')

invoice_totals = df.groupby('Invoice')['Revenue'].sum()
aov_median = invoice_totals.median()
aov_mean   = invoice_totals.mean()
avg_items  = df.groupby('Invoice')['Quantity'].sum().mean()

k1,k2,k3,k4,k5 = st.columns(5)
k1.metric('💰 Loyalty Revenue',  f'£{df["Revenue"].sum():,.0f}')
k2.metric('📦 Total Orders',      f'{df["Invoice"].nunique():,.0f}')
k3.metric('👤 Active Customers',  f'{df["CustomerID"].nunique():,.0f}')
k4.metric('🛒 Median AOV',        f'£{aov_median:,.2f}', help=f'Median order value. Mean £{aov_mean:,.2f} skewed by wholesale.')
k5.metric('📏 Avg Items / Order', f'{avg_items:.1f}', help='Avg units per invoice — distinct from AOV.')



if page == '📊 Overview':
    st.markdown('## 📊 Revenue Overview')
    monthly = df.groupby('InvoiceMonth')['Revenue'].sum().reset_index()
    fig_rev = px.line(monthly, x='InvoiceMonth', y='Revenue',
                      title='Monthly Revenue — Loyalty Customers',
                      color_discrete_sequence=['#63b3ed'])
    fig_rev.update_traces(line_width=2.5, fill='tozeroy', fillcolor='rgba(99,179,237,0.08)')
    apply_theme(fig_rev)
    dec_row = monthly[monthly['InvoiceMonth'].astype(str).str.startswith('2011-12')]
    if not dec_row.empty:
        fig_rev.add_annotation(x=dec_row['InvoiceMonth'].values[0], y=dec_row['Revenue'].values[0],
            text='⚠ Partial (ends Dec 9)', showarrow=True, arrowhead=2, ax=50, ay=-40,
            bgcolor='#4a2f0a', bordercolor='#ed8936', font_color='#ffffff')
    st.plotly_chart(fig_rev, use_container_width=True)

    col_l, col_r = st.columns(2)
    with col_l:
        fig_top = px.bar(top_products, x='Revenue', y='Description', orientation='h',
                         title='Top 10 Products by Revenue',
                         color='Revenue', color_continuous_scale='Blues')
        apply_theme(fig_top, categoryorder_y='total ascending')
        st.plotly_chart(fig_top, use_container_width=True)
    with col_r:
        yearly = df.groupby('InvoiceYear')['Revenue'].sum().reset_index()
        yearly['InvoiceYear'] = yearly['InvoiceYear'].astype(str)
        fig_yr = px.bar(yearly, x='InvoiceYear', y='Revenue', title='Revenue by Year',
                        color_discrete_sequence=['#667eea'])
        apply_theme(fig_yr)
        st.plotly_chart(fig_yr, use_container_width=True)

    st.markdown(f'<div class="insight-box">ℹ️ <b>Basket Size vs AOV:</b> Median AOV = <b>£{aov_median:,.2f}</b>. Mean AOV = £{aov_mean:,.2f} — inflated by wholesale bulk orders. Avg items/order: <b>{avg_items:.1f} units</b>. These are distinct metrics.</div>', unsafe_allow_html=True)

elif page == '👥 Customer Segments':
    st.markdown('## 👥 RFM Customer Segmentation')
    COLOR_MAP = {
        'Champions':'#63b3ed','Loyal Customers':'#667eea','At Risk':'#fc8181',
        'Cannot Lose Them':'#e53e3e','About to Sleep':'#f6ad55','Promising':'#68d391',
        'Recent Customers':'#4fd1c7','Potential Loyalists':'#b794f4',
        'Need Attention':'#fbd38d','Lost':'#a0aec0'
    }
    seg_counts = rfm['Segment'].value_counts().reset_index()
    seg_counts.columns = ['Segment','Customers']
    fig_seg = px.bar(
        seg_counts.sort_values('Customers'),
        x='Customers', y='Segment', orientation='h',
        title='Customer Count by Segment',
        color='Segment', color_discrete_map=COLOR_MAP, text='Customers'
    )
    fig_seg.update_traces(textposition='outside', textfont_color='#ffffff')
    fig_seg.update_layout(showlegend=False, **CHART_THEME)
    fig_seg.update_xaxes(**AXIS_STYLE)
    fig_seg.update_yaxes(**AXIS_STYLE, categoryorder='total ascending')
    st.plotly_chart(fig_seg, use_container_width=True)
    with st.expander('📋 Segment Definitions & Thresholds'):
        st.dataframe(seg_defs, use_container_width=True, hide_index=True)

elif page == '🔄 Cohort Retention':
    st.markdown('## 🔄 Cohort Retention Analysis')
    df_cohort = df.copy()
    df_cohort['CohortMonth']   = df_cohort.groupby('CustomerID')['InvoiceDate'].transform('min').dt.to_period('M')
    df_cohort['InvoiceMonth2'] = df_cohort['InvoiceDate'].dt.to_period('M')
    df_cohort['MonthOffset']   = (df_cohort['InvoiceMonth2'] - df_cohort['CohortMonth']).apply(lambda x: x.n)
    cohort_group = df_cohort.groupby(['CohortMonth','MonthOffset'])['CustomerID'].nunique().reset_index()
    cohort_pivot = cohort_group.pivot(index='CohortMonth', columns='MonthOffset', values='CustomerID')
    retention    = cohort_pivot.divide(cohort_pivot[0], axis=0).round(3).fillna(0)
    dec2010_ret  = retention.loc['2010-12', 3] if ('2010-12' in retention.index and 3 in retention.columns) else None
    avg_3m       = retention[3].replace(0, float('nan')).mean() if 3 in retention.columns else None
    m1, m2 = st.columns(2)
    m1.metric('Dec-2010 Cohort — Month 3 Retention', f'{dec2010_ret:.1%}' if dec2010_ret else 'N/A')
    m2.metric('Avg 3-Month Retention (All Cohorts)',  f'{avg_3m:.1%}'      if avg_3m      else 'N/A')
    st.markdown('<div class="finding">📌 <b>Finding:</b> Dec-2010 cohort drop reflects seasonal gift-buyers. Mid-2011 cohorts show stronger retention. Retention stabilises ~35% after Month 1. <b>Action:</b> reactivation campaigns at Month 1–2 window.</div>', unsafe_allow_html=True)
    ret3 = retention[3].replace(0, float('nan')).dropna().reset_index()
    ret3.columns = ['CohortMonth', 'Month3Retention']
    ret3['CohortMonth'] = ret3['CohortMonth'].astype(str)
    ret3['Pct'] = (ret3['Month3Retention'] * 100).round(1)
    fig_ret = px.bar(ret3, x='CohortMonth', y='Pct',
                     title='3-Month Retention Rate by Cohort (%)',
                     color='Pct', color_continuous_scale='Blues',
                     labels={'Pct':'Retention %','CohortMonth':'Cohort'}, text='Pct')
    fig_ret.update_traces(texttemplate='%{text}%', textposition='outside', textfont_color='#ffffff')
    fig_ret.update_layout(coloraxis_showscale=False, **CHART_THEME)
    fig_ret.update_xaxes(**AXIS_STYLE, tickangle=45)
    fig_ret.update_yaxes(**AXIS_STYLE)
    st.plotly_chart(fig_ret, use_container_width=True)

elif page == '↩️ Returns Analysis':
    st.markdown('## ↩️ Returns Analysis')
    st.markdown('<div class="insight-box">ℹ️ Returns are split into two distinct categories. Mixing them produces misleading product-quality signals.</div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(['🔴 Customer Returns — Product Quality Signal', '🟡 Operational Losses — Warehouse Write-offs'])
    with tab1:
        top_cr = (customer_returns.groupby('Description')['Quantity']
                  .count().sort_values(ascending=False).head(10)
                  .reset_index().rename(columns={'Quantity':'ReturnCount'}))
        fig_cr = px.bar(top_cr, x='ReturnCount', y='Description', orientation='h',
                        title='Top 10 Customer Returns (Product Quality Signal)',
                        color='ReturnCount', color_continuous_scale='Reds', text='ReturnCount')
        fig_cr.update_traces(textposition='outside', textfont_color='#ffffff')
        fig_cr.update_layout(showlegend=False, coloraxis_showscale=False, **CHART_THEME)
        fig_cr.update_xaxes(**AXIS_STYLE)
        fig_cr.update_yaxes(**AXIS_STYLE, categoryorder='total ascending')
        st.plotly_chart(fig_cr, use_container_width=True)
    with tab2:
      
        top_ol = (op_losses.groupby('Category')['Quantity']
                  .sum().abs().sort_values(ascending=False)
                  .reset_index().rename(columns={'Quantity':'UnitsLost'}))
        fig_ol = px.bar(top_ol, x='UnitsLost', y='Category', orientation='h',
                        title='Operational Losses by Root Cause Category',
                        color='UnitsLost', color_continuous_scale='Oranges', text='UnitsLost')
        fig_ol.update_traces(textposition='outside', textfont_color='#ffffff')
        fig_ol.update_layout(showlegend=False, coloraxis_showscale=False, **CHART_THEME)
        fig_ol.update_xaxes(**AXIS_STYLE)
        fig_ol.update_yaxes(**AXIS_STYLE, categoryorder='total ascending')
        st.plotly_chart(fig_ol, use_container_width=True)
elif page == '🌍 Country Performance':
    st.markdown('## 🌍 Country Performance')
    country_perf = (df.groupby('Country').agg(
        Revenue=('Revenue','sum'), Orders=('Invoice','nunique'), Customers=('CustomerID','nunique')
    ).reset_index().sort_values('Revenue', ascending=False))
    country_perf['AOV'] = (country_perf['Revenue'] / country_perf['Orders']).round(2)
    col_l, col_r = st.columns([3,2])
    with col_l:
        fig_country = px.bar(country_perf.head(15), x='Revenue', y='Country',
                             orientation='h', title='Top 15 Countries by Revenue',
                             color='Revenue', color_continuous_scale='Blues')
        apply_theme(fig_country, categoryorder_y='total ascending')
        st.plotly_chart(fig_country, use_container_width=True)
    with col_r:
        fig_map = px.choropleth(country_perf, locations='Country', locationmode='country names',
                                color='Revenue', title='Revenue by Country',
                                color_continuous_scale='Blues')
        apply_theme(fig_map)
        st.plotly_chart(fig_map, use_container_width=True)
    st.dataframe(country_perf, use_container_width=True, hide_index=True)
