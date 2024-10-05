from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import csv

app = Flask(__name__)

def scrape_myjoyonlinetags(query, limit):
    base_url = "https://www.myjoyonline.com"
    category_urls = []
    for tag in query.split('+'):
        category_urls.extend([
            f"/tag/{tag.replace(' ', '-')}/page/{page}/"
            for page in range(1, limit + 1)
        ])

    data = []
    try:
        def scrape_articles(category_url):
            category_url = base_url + category_url
            response = requests.get(category_url)
            response.encoding = 'utf-8'
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            article_list = soup.find('div', {'class': 'col-lg-3 col-md-6 col-sm-6 col-xs-6 mb-4'}).find_all('a') 
            if not article_list:
                print("No article links found")
                return

            for article in article_list:
                article_link = article.get('href')
                if article_link is None:
                    print("Article has no link")
                    continue
                if article_link.startswith('/'):
                    article_link = base_url + article_link
                article_title = article.text.strip()
                if article_title is None:
                    print("Article has no title")
                    continue
                data.append([article_title, article_link, '', ''])

        for category_url in category_urls:
            print(f"Scraping category: {category_url}")
            scrape_articles(category_url)

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f"Error occurred while scraping: {e}"}), 500
    except Exception as e:
        return jsonify({'error': f"Error occurred while scraping: {e}"}), 500

    return data

@app.route('/scrape', methods=['POST'])
def scrape():
    query = request.form.get('query')
    limit = int(request.form.get('limit', 1))  # Default limit to 1 if not provided

    if not query.strip():
        return jsonify({'error': 'Please enter a search query'}), 400

    if limit <= 0:
        return jsonify({'error': 'Please enter a limit greater than 0'}), 400

    data = scrape_myjoyonlinetags(query, limit)
    
    if isinstance(data, list): #if data is a list then no errors were encountered
        # Save data to CSV 
        with open('scraped.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Title", "Link", "Date", "Excerpt"])
            writer.writerows(data)

        return jsonify({'message': 'Scraping complete. Data saved to scraped.csv'}), 200
    else:
        #if data is not a list then data is a flask response signifying an error
        return data

if __name__ == '__main__':
    app.run(debug=True)
