from selenium import webdriver
import time
import numpy as np
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import re
from datetime import date, datetime
import sqlite3

#Install Driver
driver = webdriver.Chrome(ChromeDriverManager().install())

#Specify URL
search_url = "https://shopee.co.id/han_river_official" 

driver.get(search_url)
time.sleep(10) #sleep_between_interactions

#GET SHOP INFORMATION

#Shop Name
shop_name = driver.find_element_by_xpath("//h1[contains(@class,'section-seller-overview-horizontal__portrait-name')]").text

#Shop Logo
shop_logo = driver.find_element_by_xpath("//img[contains(@class,'shopee-avatar__img')]").get_attribute('src')

#Number of Products
num_product = int(driver.find_element_by_xpath("//div[contains(@class,'section-seller-overview__item-text-value')]").text)

#Shop Tagline
shop_tagline = driver.find_element_by_xpath("//div[contains(@class,'shop-page-shop-description')]/span").text
shop_tagline = shop_tagline.split('\n')
shop_tagline = " ".join(shop_tagline)

#Save to database
conn = sqlite3.connect('shopee_scraper.db')
shop = {"shop_name" : [shop_name], "shop_logo" : [shop_logo], "number_of_products" : [num_product], "shop_tagline" : [shop_tagline], "scraped_at" : [datetime.now()]}
df = pd.DataFrame(shop)
df.to_sql('shop_information', conn, if_exists='replace', index=False)
conn.close()

print("Shop Information")
print("Shop Name: {0}".format(shop_name))
print("Shop Logo: {0}".format(shop_logo))
print("Number of Products: {0}".format(num_product))
print("Shop Tagline: {0}".format(shop_tagline))
time.sleep(5) #sleep_between_interactions

#GET PRODUCTS INFORMATION 

#Define Table
products_info = {"name":[],"category":[],"description":[],"price":[],"weight":[],"stock":[],"image_urls":[]}

#Go to product section
driver.find_element_by_xpath("//div[contains(@class,'section-seller-overview__item-icon-wrapper')]").click()
time.sleep(1) #sleep_between_interactions

#Get categories
primary_category_path = "//div[contains(@class,'shopee-facet-filter')]/div[contains(@class,'shopeee-filter-group__body')]"
categories_pr = driver.find_elements_by_xpath(primary_category_path + "/div[contains(@class,'shopee-checkbox-filter')]/div[contains(@class,'shopee-checkbox')]/label[contains(@class,'shopee-checkbox__control')]/span[contains(@class,'shopee-checkbox__label')]")
categories_sc = driver.find_elements_by_xpath(primary_category_path + "/div[contains(@class,'stardust-dropdown folding-items__toggle')]/div[contains(@class,'stardust-dropdown__item-body')]/div[contains(@class,'folding-items__folded-items')]/div[contains(@class,'shopee-checkbox-filter')]/div[contains(@class,'shopee-checkbox')]/label[contains(@class,'shopee-checkbox__control')]/span[contains(@class,'shopee-checkbox__label')]")
categories = categories_pr + categories_sc

#Iterate Over Categories
for cat in range(len(categories)):
    categories_pr = driver.find_elements_by_xpath(primary_category_path + "/div[contains(@class,'shopee-checkbox-filter')]/div[contains(@class,'shopee-checkbox')]/label[contains(@class,'shopee-checkbox__control')]/span[contains(@class,'shopee-checkbox__label')]")
    categories_sc = driver.find_elements_by_xpath(primary_category_path + "/div[contains(@class,'stardust-dropdown folding-items__toggle')]/div[contains(@class,'stardust-dropdown__item-body')]/div[contains(@class,'folding-items__folded-items')]/div[contains(@class,'shopee-checkbox-filter')]/div[contains(@class,'shopee-checkbox')]/label[contains(@class,'shopee-checkbox__control')]/span[contains(@class,'shopee-checkbox__label')]")
    categories = categories_pr + categories_sc
    categories[cat].click()
    time.sleep(3) #sleep_between_interactions

    #Get Pages
    pages = driver.find_elements_by_xpath("//div[contains(@class,'shopee-page-controller')]/button[contains(@class,'shopee-button-solid')]")

    product_category = re.match("^[^\(,]*", categories[cat].text)[0].strip()
    #Iterate Over Pages
    for p in range(len(pages)):
        page = driver.find_elements_by_xpath("//div[contains(@class,'shopee-page-controller')]/button[contains(@class,'shopee-button-solid')]")[p]
        page.click()
        time.sleep(1) #sleep_between_interactions

        products = driver.find_elements_by_xpath("//div[contains(@class,'shop-search-result-view__item')]")

        #Iterate Over Products
        for pr in range(len(products)):
            product = driver.find_elements_by_xpath("//div[contains(@class,'shop-search-result-view__item')]")[pr]
            product.click()
            time.sleep(1) #sleep_between_interactions

            #Get Product Name
            product_name = driver.find_element_by_xpath("//div[contains(@class,'attM6y')]").text
            products_info["name"].append(product_name)

            #Get Product Category
            products_info["category"].append(product_category)

            #Get Product Description
            product_description = driver.find_element_by_xpath("//div[contains(@class,'_3yZnxJ')]").text.replace("./n",". ").replace("/n",". ")
            products_info["description"].append(product_description)

            #Get Product Price
            try: #handle interval pricing
                product_price = int(driver.find_element_by_xpath("//div[contains(@class,'Ybrg9j')]").text.replace("Rp","").replace(".",""))
                products_info["price"].append(product_price)
            except ValueError:
                number = driver.find_element_by_xpath("//div[contains(@class,'Ybrg9j')]").text.replace("Rp","").replace(".","")
                price = re.search("(\d+)(?=\s*-)", number)[0] #get minimum price from the interval
                product_price = int(price)
                products_info["price"].append(product_price)

            #Get Product Weight
            weights = driver.find_elements_by_xpath("//div[contains(@class,'aPKXeO')]")
            specs = []

            for i in range(len(weights)):
                specs.append(weights[i].find_element_by_xpath("label").text)

            if "Berat Produk" in specs:
                for i in range(len(weights)):
                    if weights[i].find_element_by_xpath("label").text == "Berat Produk":
                        weight = weights[i].find_element_by_xpath("div").text
                        if "kg" in re.findall("kg", weight):
                            weight = float(weight.replace("kg", "")) * 1000 #convert kg to gram
                        else:
                            weight = float(weight.replace("g", ""))
                        products_info['weight'].append(weight)
                        break
            else:
                products_info['weight'].append(np.nan)
            
            #Get Product Stock
            stocks = driver.find_elements_by_xpath("//div[contains(@class,'aPKXeO')]")
            specs = []

            for i in range(len(stocks)):
                specs.append(stocks[i].find_element_by_xpath("label").text)

            if "Stok" in specs or "Stok Diskon" in specs or "Stok Lain" in specs:
                for i in range(len(stocks)):
                    if stocks[i].find_element_by_xpath("label").text == "Stok":
                        stock = int(stocks[i].find_element_by_xpath("div").text)
                        products_info['stock'].append(stock)
                        break
                    elif stocks[i].find_element_by_xpath("label").text == "Stok Diskon":
                        stock_d = int(stocks[i].find_element_by_xpath("div").text)
                    elif stocks[i].find_element_by_xpath("label").text == "Stok Lain":
                        stock_l = int(stocks[i].find_element_by_xpath("div").text)
                        products_info['stock'].append(stock_d + stock_l)
                        break
            else:
                products_info['stock'].append(np.nan)

            #Get Image URLs
            driver.find_element_by_xpath("//div[contains(@class,'ApRQXC')]").click()
            time.sleep(1) #sleep_between_interactions
            images = driver.find_elements_by_xpath("//div[contains(@class,'_3-_YTZ _2fdy4G')]")
            urls = []

            for i in range(len(images)):
                image = driver.find_elements_by_xpath("//div[contains(@class,'_3-_YTZ _2fdy4G')]")[i]
                image.click()
                try: #handle video
                    style = driver.find_element_by_xpath("//div[contains(@class,'_1PrnIh _2GchKS')]").get_attribute('style')
                    style_url = style.split(";")[0]
                    regex_url = "((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*"
                    url = re.search(regex_url, style_url)[0]
                    urls.append(url)
                except:
                    video = driver.find_element_by_xpath("//video").get_attribute('src')
                    urls.append(video)

            image_urls = ",".join(urls)
            products_info['image_urls'].append(image_urls)

            #Get Back
            driver.back()
            time.sleep(3) #sleep_between_interactions
    
    if cat <= 3:
        driver.find_element_by_xpath(primary_category_path + "/div[contains(@class,'stardust-dropdown folding-items__toggle')]/div[contains(@class,'stardust-dropdown__item-header')]/div[contains(@class,'shopee-filter-group__toggle-btn')]").click()
        time.sleep(1) #sleep_between_interactions
    categories_pr = driver.find_elements_by_xpath(primary_category_path + "/div[contains(@class,'shopee-checkbox-filter')]/div[contains(@class,'shopee-checkbox')]/label[contains(@class,'shopee-checkbox__control')]/span[contains(@class,'shopee-checkbox__label')]")
    categories_sc = driver.find_elements_by_xpath(primary_category_path + "/div[contains(@class,'stardust-dropdown folding-items__toggle')]/div[contains(@class,'stardust-dropdown__item-body')]/div[contains(@class,'folding-items__folded-items')]/div[contains(@class,'shopee-checkbox-filter')]/div[contains(@class,'shopee-checkbox')]/label[contains(@class,'shopee-checkbox__control')]/span[contains(@class,'shopee-checkbox__label')]")
    categories = categories_pr + categories_sc
    categories[cat].click()
    time.sleep(3) #sleep_between_interactions

#SAVE RESULTS TO EXCEL AND LOCAL DATABASE

#Convert dictionary to dataframe
df = pd.DataFrame(products_info, columns=['name', 'category', 'description', 'price', 'weight', 'stock', 'image_urls'])
df = df.drop_duplicates()

#Get today's date and time
today = date.today().strftime("%Y-%m-%d")
now = str(datetime.now().hour) + " " + str(datetime.now().minute)

#Save to excel by current datetime 
writer = pd.ExcelWriter("scraping result {2} ({0} {1}).xlsx".format(today, now, shop_name), engine='xlsxwriter')
df.to_excel(writer, sheet_name="Scraping Result ({0})".format(today), index = None, na_rep='NA')
writer.save()

#Save to database
conn = sqlite3.connect('shopee_scraper.db')
df.to_sql('products_information', conn, if_exists='replace', index=False)
conn.close()