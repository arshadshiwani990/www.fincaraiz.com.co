import scrapy
from scrapy import Request

class SuppliersSpider(scrapy.Spider):
	name = "fincaraiz"

	custom_settings = {
		'FEEDS': {
			'fincaraiz_rent.csv': {
				'format': 'csv',
				'encoding': 'utf-8-sig',
				'overwrite': True,
			},
		},
	}
	headers = {
		'accept': '*/*',
		'accept-language': 'en-US,en;q=0.9',
		'content-type': 'application/json',
		'origin': 'https://www.fincaraiz.com.co',
		'referer': 'https://www.fincaraiz.com.co/venta',
		'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
		'sec-ch-ua-mobile': '?0',
		'sec-ch-ua-platform': '"Windows"',
		'sec-fetch-dest': 'empty',
		'sec-fetch-mode': 'cors',
		'sec-fetch-site': 'same-site',
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
	}

	start_urls = ['https://fasteignir.visir.is']

	price_ranges = [
		{'minPrice': 150000099, 'maxPrice': 200000000},
		{'minPrice': 0, 'maxPrice': 150000000},
		# {'minPrice': 30000000, 'maxPrice': 40000000},
		# Add more price ranges as needed
	]

	def parse(self, response):
		for price_range in self.price_ranges:
			for i in range(2, 3):  # Assuming operation_type_id values are 1 and 2
				data = f'{{"variables":{{"rows":21,"params":{{"page":1,"order":2,"operation_type_id":{i},"minPrice":{price_range["minPrice"]},"maxPrice":{price_range["maxPrice"]},"currencyID":4,"m2Currency":4}},"page":2,"source":10}},"query":""}}'
				url = "https://search-service.fincaraiz.com.co/api/v1/properties/search"

				yield Request(
					url,
					callback=self.category_parse,
					method="POST",
					body=data,
					headers=self.headers,
					meta={'category_id': i, 'page': 1, 'price_range': price_range}
				)
				# break

	def category_parse(self, response):
		category_id = response.meta['category_id']
		page = int(response.meta['page'])
		price_range = response.meta['price_range']

		items = response.json().get('hits', {}).get('hits', [])
		total = int(response.json().get('hits', {}).get('total').get('value'))
		print(total)
		total_pages = int(total / 20) + 1

		for item in items:
			try:
				results = {}
				listing = item.get('_source', {}).get('listing', {})
				results['title'] = listing.get('title', '')

				locations = listing.get('locations', {})
				results['country'] = locations.get('country', [{}])[0].get('name', '')
				results['city'] = locations.get('city', [{}])[0].get('name', '')
				results['state'] = locations.get('state', [{}])[0].get('name', '')

				city = locations.get('city', [{}])[0].get('name', '')
				state = locations.get('state', [{}])[0].get('name', '')
				neighbourhood = locations.get('neighbourhood', [])
				if neighbourhood:
					main_location = neighbourhood[0].get('name', '') + ',' + city + ',' + state
				else:
					main_location = city + ',' + state

				results['main_location'] = main_location
				neighbourhood_list = ','.join([neigh.get('name', '') for neigh in locations.get('neighbourhood', [])])
				results['neighbourhood'] = neighbourhood_list

				facilities = listing.get('facilities', [])
				facilities_list = ','.join([facility.get('name', '') or '' for facility in facilities])
				results['facilities'] = facilities_list

				results['address'] = listing.get('address', '')
				results['description'] = listing.get('description', '')

				price = listing.get('price', {}).get('amount', '')
				results['price'] = price

				technicalSheet = listing.get('technicalSheet', [])
				if technicalSheet:
					for tech_item in technicalSheet:
						field = tech_item.get('field', '')
						value = tech_item.get('value', '')
						results[field] = value

				results['bathrooms'] = listing.get('bathrooms', [''])
				results['bedrooms'] = listing.get('bedrooms', [''])
				results['rooms'] = listing.get('rooms', [''])
				results['latitude'] = listing.get('latitude')
				results['longitude'] = listing.get('longitude')
				results['m2'] = listing.get('m2')
				commercial_units = listing.get('commercial_units', [])
				new_data_list = []
				for unit in commercial_units:
					new_item = {
						'id': unit.get('id'),
						'title': unit.get('title'),
						'bedrooms': unit.get('bedrooms'),
						'bathrooms': unit.get('bathrooms'),
						'm2': unit.get('m2'),
						'price': unit.get('price', {}).get('amount', '')
					}
					new_data_list.append(new_item)

				results['commercial_units'] = new_data_list
				results['property_type'] = listing.get('property_type').get('name')
				if category_id == 1:
					results['listing'] = 'Sale'

				if category_id == 2:
					results['listing'] = 'Rent'
				results['category_id'] = category_id
				results['price_range'] = price_range
				yield results
			except:
				pass
		if page < total_pages:
			data = f'{{"variables":{{"rows":21,"params":{{"page":{page + 1},"order":2,"operation_type_id":{category_id},"minPrice":{price_range["minPrice"]},"maxPrice":{price_range["maxPrice"]},"currencyID":4,"m2Currency":4}},"page":{page + 1},"source":10}},"query":""}}'
			url = "https://search-service.fincaraiz.com.co/api/v1/properties/search"
			yield Request(
				url,
				callback=self.category_parse,
				method="POST",
				body=data,
				headers=self.headers,
				meta={'category_id': category_id, 'page': page + 1, 'price_range': price_range}
			)
