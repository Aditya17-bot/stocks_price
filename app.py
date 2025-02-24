from flask import Flask, render_template, request, jsonify
import yfinance as yf
from datetime import datetime
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Remove the SECRET_KEY configuration since it's not needed
app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'

# Dictionary of Nifty 200 stocks grouped by sectors
NIFTY200_STOCKS = {
    'Financial Services': [
        'HDFCBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 
        'BAJFINANCE.NS', 'HDFCLIFE.NS', 'SBILIFE.NS', 'BAJAJFINSV.NS', 'ICICIPRULI.NS',
        'ICICIGI.NS', 'CHOLAFIN.NS', 'MUTHOOTFIN.NS', 'AUBANK.NS', 'FEDERALBNK.NS',
        'INDIANB.NS', 'BANDHANBNK.NS', 'PFC.NS', 'RECLTD.NS', 'IDFCFIRSTB.NS',
        'CANBK.NS', 'BANKBARODA.NS', 'PNB.NS'
    ],
    'IT & Technology': [
        'TCS.NS', 'INFY.NS', 'HCLTECH.NS', 'WIPRO.NS', 'TECHM.NS', 'LTIM.NS',
        'PERSISTENT.NS', 'COFORGE.NS', 'LTTS.NS', 'MPHASIS.NS', 'ZOMATO.NS',
        'NAUKRI.NS', 'PAYTM.NS', 'POLICYBZR.NS'
    ],
    'Oil, Gas & Energy': [
        'RELIANCE.NS', 'ONGC.NS', 'BPCL.NS', 'ADANIGREEN.NS', 'NTPC.NS', 
        'POWERGRID.NS', 'TATAPOWER.NS', 'IOC.NS', 'GAIL.NS', 'PETRONET.NS',
        'TORNTPOWER.NS', 'ADANIPOWER.NS'
    ],
    'Automobile & Auto Components': [
        'TATAMOTORS.NS', 'M&M.NS', 'MARUTI.NS', 'BAJAJ-AUTO.NS', 'EICHERMOT.NS',
        'ASHOKLEY.NS', 'BHARATFORG.NS', 'MOTHERSON.NS', 'BALKRISIND.NS', 'MRF.NS',
        'BOSCHLTD.NS', 'TVSMOTOR.NS'
    ],
    'Metal, Mining & Materials': [
        'TATASTEEL.NS', 'HINDALCO.NS', 'JSWSTEEL.NS', 'ADANIENT.NS', 'VEDL.NS',
        'JINDALSTEL.NS', 'APLAPOLLO.NS', 'NATIONALUM.NS', 'NMDC.NS', 'COALINDIA.NS'
    ],
    'FMCG & Consumer': [
        'ITC.NS', 'HINDUNILVR.NS', 'BRITANNIA.NS', 'NESTLEIND.NS', 'DABUR.NS',
        'COLPAL.NS', 'GODREJCP.NS', 'MARICO.NS', 'TATACONSUM.NS', 'VBL.NS',
        'MCDOWELL-N.NS', 'UBL.NS'
    ],
    'Pharma & Healthcare': [
        'APOLLOHOSP.NS', 'DIVISLAB.NS', 'DRREDDY.NS', 'CIPLA.NS', 'SUNPHARMA.NS',
        'BIOCON.NS', 'ALKEM.NS', 'TORNTPHARM.NS', 'AUROPHARMA.NS', 'LUPIN.NS',
        'GLAND.NS', 'MAXHEALTH.NS'
    ],
    'Construction & Infrastructure': [
        'LT.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'DLF.NS', 'GODREJPROP.NS',
        'OBEROIRLTY.NS', 'PRESTIGE.NS', 'PHOENIXLTD.NS', 'IRCTC.NS', 'CONCOR.NS',
        'SUPREMEIND.NS'
    ],
    'Cement & Building Materials': [
        'ULTRACEMCO.NS', 'SHREECEM.NS', 'GRASIM.NS', 'AMBUJACEM.NS', 'ACC.NS',
        'RAMCOCEM.NS', 'JKCEMENT.NS', 'NUVOCO.NS'
    ],
    'Telecom & Media': [
        'BHARTIARTL.NS', 'IDEA.NS', 'ZEEL.NS', 'PVR.NS', 'NXTDIGITAL.NS'
    ],
    'Retail & Consumer Services': [
        'TITAN.NS', 'ASIANPAINT.NS', 'JUBLFOOD.NS', 'DMART.NS', 'TRENT.NS',
        'SHOPERSTOP.NS', 'ABFRL.NS', 'BATAINDIA.NS', 'RELAXO.NS'
    ],
    'Chemicals & Fertilizers': [
        'PIDILITIND.NS', 'BERGEPAINT.NS', 'FLUOROCHEM.NS', 'CLEAN.NS', 'SRF.NS',
        'UPL.NS', 'COROMANDEL.NS', 'DEEPAKFERT.NS'
    ],
    'Manufacturing & Capital Goods': [
        'HAVELLS.NS', 'SIEMENS.NS', 'ABB.NS', 'BEL.NS', 'CGPOWER.NS',
        'GRINDWELL.NS', 'CUMMINSIND.NS', 'THERMAX.NS'
    ]
}

# Add this dictionary after NIFTY200_STOCKS
INDICES = {
    'NIFTY 50': '^NSEI',
    'BANK NIFTY': '^NSEBANK',
    'NIFTY IT': '^CNXIT',
    'NIFTY AUTO': '^CNXAUTO',
    'NIFTY PHARMA': '^CNXPHARMA',
    'NIFTY METAL': '^CNXMETAL',
    'NIFTY FMCG': '^CNXFMCG',
    'NIFTY REALTY': '^CNXREALTY'
}

# Add this dictionary after INDICES
STOCK_SUGGESTIONS = {
    'ADANIENT': 'Adani Enterprises',
    'ADANIPORTS': 'Adani Ports & SEZ',
    'APOLLOHOSP': 'Apollo Hospitals',
    'ASIANPAINT': 'Asian Paints',
    'AXISBANK': 'Axis Bank',
    'BAJAJ-AUTO': 'Bajaj Auto',
    'BAJFINANCE': 'Bajaj Finance',
    'BAJAJFINSV': 'Bajaj Finserv',
    'BPCL': 'Bharat Petroleum',
    'BHARTIARTL': 'Bharti Airtel',
    'BRITANNIA': 'Britannia Industries',
    'CIPLA': 'Cipla',
    'COALINDIA': 'Coal India',
    'DIVISLAB': 'Divi\'s Laboratories',
    'DRREDDY': 'Dr Reddy\'s Laboratories',
    'EICHERMOT': 'Eicher Motors',
    'GRASIM': 'Grasim Industries',
    'HCLTECH': 'HCL Technologies',
    'HDFCBANK': 'HDFC Bank',
    'HDFCLIFE': 'HDFC Life Insurance',
    'HEROMOTOCO': 'Hero MotoCorp',
    'HINDALCO': 'Hindalco Industries',
    'HINDUNILVR': 'Hindustan Unilever',
    'ICICIBANK': 'ICICI Bank',
    'INDUSINDBK': 'IndusInd Bank',
    'INFY': 'Infosys',
    'ITC': 'ITC Limited',
    'JSWSTEEL': 'JSW Steel',
    'KOTAKBANK': 'Kotak Mahindra Bank',
    'LT': 'Larsen & Toubro',
    'M&M': 'Mahindra & Mahindra',
    'MARUTI': 'Maruti Suzuki',
    'NESTLEIND': 'Nestle India',
    'NTPC': 'NTPC Limited',
    'ONGC': 'Oil & Natural Gas Corporation',
    'POWERGRID': 'Power Grid Corporation',
    'RELIANCE': 'Reliance Industries',
    'SBILIFE': 'SBI Life Insurance',
    'SBIN': 'State Bank of India',
    'SUNPHARMA': 'Sun Pharmaceutical',
    'TCS': 'Tata Consultancy Services',
    'TATACONSUM': 'Tata Consumer Products',
    'TATAMOTORS': 'Tata Motors',
    'TATASTEEL': 'Tata Steel',
    'TECHM': 'Tech Mahindra',
    'TITAN': 'Titan Company',
    'ULTRACEMCO': 'UltraTech Cement',
    'UPL': 'UPL Limited',
    'WIPRO': 'Wipro',
    'ACC': 'ACC Limited',
    'ADANIGREEN': 'Adani Green Energy',
    'ADANIPOWER': 'Adani Power',
    'ALKEM': 'Alkem Laboratories',
    'AMBUJACEM': 'Ambuja Cements',
    'AUROPHARMA': 'Aurobindo Pharma',
    'AUBANK': 'AU Small Finance Bank',
    'ABFRL': 'Aditya Birla Fashion',
    'BANDHANBNK': 'Bandhan Bank',
    'BANKBARODA': 'Bank of Baroda',
    'BATAINDIA': 'Bata India',
    'BERGEPAINT': 'Berger Paints',
    'BIOCON': 'Biocon',
    'BOSCHLTD': 'Bosch',
    'CANBK': 'Canara Bank',
    'CGPOWER': 'CG Power',
    'CHOLAFIN': 'Cholamandalam Investment',
    'COFORGE': 'Coforge Limited',
    'COLPAL': 'Colgate-Palmolive',
    'CONCOR': 'Container Corporation',
    'COROMANDEL': 'Coromandel International',
    'DABUR': 'Dabur India',
    'DEEPAKFERT': 'Deepak Fertilisers',
    'DLF': 'DLF Limited',
    'FEDERALBNK': 'Federal Bank',
    'FLUOROCHEM': 'Gujarat Fluorochemicals',
    'GAIL': 'GAIL India',
    'GLAND': 'Gland Pharma',
    'GODREJCP': 'Godrej Consumer Products',
    'GODREJPROP': 'Godrej Properties',
    'GRINDWELL': 'Grindwell Norton',
    'HAVELLS': 'Havells India',
    'IDFCFIRSTB': 'IDFC First Bank',
    'INDIANB': 'Indian Bank',
    'IOC': 'Indian Oil Corporation',
    'IRCTC': 'Indian Railway Catering',
    'JINDALSTEL': 'Jindal Steel & Power',
    'JKCEMENT': 'JK Cement',
    'JUBLFOOD': 'Jubilant FoodWorks',
    'LTIM': 'LTIMindtree',
    'LTTS': 'L&T Technology Services',
    'LUPIN': 'Lupin Limited',
    'MARICO': 'Marico',
    'MAXHEALTH': 'Max Healthcare',
    'MCDOWELL-N': 'United Spirits',
    'MOTHERSON': 'Motherson Sumi Systems',
    'MPHASIS': 'Mphasis',
    'MRF': 'MRF Limited',
    'MUTHOOTFIN': 'Muthoot Finance',
    'NATIONALUM': 'National Aluminium',
    'NAUKRI': 'Info Edge India',
    'NMDC': 'NMDC Limited',
    'NUVOCO': 'Nuvoco Vistas Corp',
    'OBEROIRLTY': 'Oberoi Realty',
    'PAYTM': 'One 97 Communications',
    'PERSISTENT': 'Persistent Systems',
    'PETRONET': 'Petronet LNG',
    'PFC': 'Power Finance Corporation',
    'PIDILITIND': 'Pidilite Industries',
    'PHOENIXLTD': 'Phoenix Mills',
    'POLICYBZR': 'PB Fintech',
    'PNB': 'Punjab National Bank',
    'PRESTIGE': 'Prestige Estates',
    'PVR': 'PVR Limited',
    'RAMCOCEM': 'Ramco Cements',
    'RECLTD': 'REC Limited',
    'RELAXO': 'Relaxo Footwears',
    'SHREECEM': 'Shree Cement',
    'SIEMENS': 'Siemens',
    'SHOPERSTOP': 'Shoppers Stop',
    'SRF': 'SRF Limited',
    'SUPREMEIND': 'Supreme Industries',
    'TATAPOWER': 'Tata Power',
    'THERMAX': 'Thermax',
    'TORNTPHARM': 'Torrent Pharmaceuticals',
    'TORNTPOWER': 'Torrent Power',
    'TRENT': 'Trent Limited',
    'TVSMOTOR': 'TVS Motor Company',
    'UBL': 'United Breweries',
    'VEDL': 'Vedanta Limited',
    'VBL': 'Varun Beverages',
    'ZEEL': 'Zee Entertainment',
    'ZOMATO': 'Zomato Limited'
}

@app.route('/')
def index():
    try:
        # Get Nifty 50 and Bank Nifty data
        nifty50 = yf.Ticker('^NSEI')
        banknifty = yf.Ticker('^NSEBANK')
        
        nifty_data = {
            'price': nifty50.info['regularMarketPrice'],
            'change': nifty50.info['regularMarketChangePercent'],
            'high': nifty50.info['dayHigh'],
            'low': nifty50.info['dayLow']
        }
        
        bank_data = {
            'price': banknifty.info['regularMarketPrice'],
            'change': banknifty.info['regularMarketChangePercent'],
            'high': banknifty.info['dayHigh'],
            'low': banknifty.info['dayLow']
        }
        
        return render_template('index.html', 
                             sectors=NIFTY200_STOCKS.keys(),
                             indices=INDICES.keys(),
                             nifty_data=nifty_data,
                             bank_data=bank_data)
    except Exception as e:
        print(f"Error fetching index data: {e}")
        return render_template('index.html', 
                             sectors=NIFTY200_STOCKS.keys(),
                             indices=INDICES.keys())

@app.route('/get_sector_prices', methods=['POST'])
def get_sector_prices():
    try:
        sector = request.form['sector']
        stocks = NIFTY200_STOCKS.get(sector, [])
        
        results = []
        for symbol in stocks:
            stock = yf.Ticker(symbol)
            info = stock.info
            results.append({
                'symbol': symbol.replace('.NS', ''),
                'company': info['longName'],
                'price': info['regularMarketPrice'],
                'change': info['regularMarketChangePercent'],
                'volume': info['regularMarketVolume'],
                'dayHigh': info['dayHigh'],
                'dayLow': info['dayLow']
            })
            
        return jsonify({
            'success': True,
            'stocks': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/get_stock_price', methods=['POST'])
def get_stock_price():
    try:
        symbol = request.form['symbol'].upper()
        # Add .NS suffix if not present
        if not symbol.endswith('.NS'):
            symbol = f"{symbol}.NS"
            
        # Find the sector for this stock
        sector = None
        for sec, stocks in NIFTY200_STOCKS.items():
            if symbol in stocks:
                sector = sec
                break
            
        stock = yf.Ticker(symbol)
        info = stock.info
        return jsonify({
            'success': True,
            'stock': {
                'symbol': symbol.replace('.NS', ''),
                'company': info['longName'],
                'sector': sector,
                'price': info['regularMarketPrice'],
                'change': info['regularMarketChangePercent'],
                'volume': info['regularMarketVolume'],
                'dayHigh': info['dayHigh'],
                'dayLow': info['dayLow']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Stock not found. Please check the symbol.'
        })

@app.route('/get_index_price', methods=['POST'])
def get_index_price():
    try:
        index_name = request.form['index']
        symbol = INDICES.get(index_name)
        if not symbol:
            raise ValueError("Invalid index selected")
            
        index = yf.Ticker(symbol)
        info = index.info
        
        return jsonify({
            'success': True,
            'index': {
                'name': index_name,
                'price': info['regularMarketPrice'],
                'change': info['regularMarketChangePercent'],
                'high': info['dayHigh'],
                'low': info['dayLow'],
                'volume': info['regularMarketVolume']
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/get_suggestions', methods=['POST'])
def get_suggestions():
    query = request.form['query'].upper()
    suggestions = []
    
    for symbol, name in STOCK_SUGGESTIONS.items():
        if query in symbol.upper() or query in name.upper():
            suggestions.append({
                'symbol': symbol,
                'name': name
            })
    
    return jsonify(suggestions[:5])  # Return top 5 matches

@app.route('/get_divergence_stocks', methods=['POST'])
def get_divergence_stocks():
    try:
        nifty_threshold = float(request.form.get('niftyPercent', 0.75))
        stock_threshold = float(request.form.get('stockPercent', 0.75))
        
        # Get Nifty 50 current data
        nifty50 = yf.Ticker('^NSEI')
        nifty_info = nifty50.info
        nifty_current = nifty_info['regularMarketPrice']
        nifty_open = nifty_info['regularMarketOpen']
        nifty_change_percent = ((nifty_current - nifty_open) / nifty_open) * 100

        # Only proceed if Nifty is up by user-specified percentage or more
        if nifty_change_percent < nifty_threshold:
            return jsonify({
                'success': True,
                'message': f'Nifty 50 up only by {nifty_change_percent:.2f}%. Waiting for {nifty_threshold}% up move.',
                'stocks': []
            })

        divergence_stocks = []
        
        # Check all stocks in NIFTY200_STOCKS
        for sector, stocks in NIFTY200_STOCKS.items():
            for symbol in stocks:
                try:
                    stock = yf.Ticker(symbol)
                    info = stock.info
                    current_price = info['regularMarketPrice']
                    open_price = info['regularMarketOpen']
                    stock_change_percent = ((current_price - open_price) / open_price) * 100

                    # If stock is down by user-specified percentage or more
                    if stock_change_percent <= -stock_threshold:
                        divergence_stocks.append({
                            'symbol': symbol.replace('.NS', ''),
                            'company': info['longName'],
                            'sector': sector,
                            'open': open_price,
                            'current': current_price,
                            'change': stock_change_percent,
                            'volume': info['regularMarketVolume']
                        })
                except Exception as e:
                    continue  # Skip stocks that fail to fetch

        return jsonify({
            'success': True,
            'nifty': {
                'open': nifty_open,
                'current': nifty_current,
                'change': nifty_change_percent
            },
            'stocks': divergence_stocks
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 