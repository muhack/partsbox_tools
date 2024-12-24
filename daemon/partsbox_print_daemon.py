#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import reduce
import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import re

import requests

class PartsboxAPI:
	'''
	Class to interact with the Partsbox API
	'''
	@staticmethod
	def get_part_id(part_url: str) -> str|None:
		'''
		Get the part ID from a URL
		'''
		regex = r'partsbox.com\/.+?\/parts\/(\w{26})'
		m = re.search(regex, part_url)
		if m:
			return m.group(1)
		return None

	@staticmethod
	def get_part_IdAnything_url(part_id: str) -> str:
		'''
		Get the URL for a part
		'''
		return f'https://partsbox.com/I{part_id}'

	def __init__(self, api_key):
		headers = {
			'Authorization': f'APIKey {api_key}',
		}
		self.s = requests.Session()
		self.s.headers.update(headers)

	def get_part_data(self, part_id) -> dict|None:
		'''
		Get single part data
		'''
		json_data = {
			'part/id': part_id,
		}
		r = self.s.post('https://api.partsbox.com/api/1/part/get', json=json_data, timeout=5)
		return r.json().get('data')

	def get_part_storage_id(self, part_data: dict) -> str|None:
		'''
		Get the storage ID from part data
		'''
		return part_data.get('part/stock', [{}])[0].get('stock/storage-id')

	def get_part_total_stock(self, part_data: dict) -> int|None:
		'''
		Get the total stock of a part
		'''
		return reduce(lambda x, y: x + y.get('stock/quantity'), part_data.get('part/stock', []), 0)

	def get_storage_data(self, storage_id: str|None) -> dict|None:
		'''
		Get data for a single storage location
		'''
		if storage_id is None:
			return None
		json_data = {
			'storage/id': storage_id,
		}
		r = self.s.post('https://api.partsbox.com/api/1/storage/get', json=json_data, timeout=5)
		return r.json().get('data')

	def get_storage_name(self, storage_data: dict|None) -> str|None:
		'''
		Get the name of a storage location
		'''
		if storage_data is None:
			return None
		return storage_data.get('storage/name')

	def get_part_csv_data(self, part_id: str) -> dict|None:
		'''
		Get data for a part like the CSV you can download from the website
		'''
		part_data = self.get_part_data(part_id)
		print(part_data)
		if not part_data:
			return None
		storage_id = self.get_part_storage_id(part_data)
		storage_data = self.get_storage_data(storage_id)
		storage_name = self.get_storage_name(storage_data)

		return {
			'Name': part_data.get('part/name'),
			'Description': part_data.get('part/description'),
			'Footprint': part_data.get('part/footprint'),
			'Manufacturer': part_data.get('part/manufacturer'),
			'MPN': part_data.get('part/mpn'),
			'Storage': storage_name,
			'Total Stock': self.get_part_total_stock(part_data),
			'URL': PartsboxAPI.get_part_IdAnything_url(part_id),
			'Meta-Parts': '', # Sorry, no easy way to get this data with the API, it seems...
		}

class PartsboxPrinterReqHandler(BaseHTTPRequestHandler):
	'''
	HTTP request handler with CORS support
	'''
	def _send_cors_headers(self):
		'''
		Sets headers required for CORS
		'''
		self.send_header('Access-Control-Allow-Origin', '*')
		self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
		self.send_header('Access-Control-Allow-Headers', 'x-api-key,Content-Type')

	def send_dict_response(self, d):
		'''
		Sends a dictionary (JSON) back to the client
		'''
		self.wfile.write(bytes(json.dumps(d), 'utf8'))

	def do_OPTIONS(self):
		self.send_response(200)
		self._send_cors_headers()
		self.end_headers()

	def do_POST(self):
		self.send_response(200)
		self._send_cors_headers()
		self.send_header('Content-Type', 'application/json')
		self.end_headers()

		dataLength = int(self.headers['Content-Length'])
		data = self.rfile.read(dataLength)

		# Parse the JSON data
		data = json.loads(data.decode('utf-8'))
		if type(data) != list:
			print(f'[E] Expected a list of urls, got {type(data)} ({data:20}...)')
			response = {}
			response['status'] = 'ERROR'
			response['message'] = 'Expected a list of URLs'
			self.send_dict_response(response)
			return

		response = {}
		response['status'] = 'OK'
		self.send_dict_response(response)

		# Process the URLs
		for url in data:
			print(f'[D] Processing URL: {url}')
			part_id = PartsboxAPI.get_part_id(url)
			if not part_id:
				print('[E] Could not get part ID')
				continue

			part_csv_data = pa.get_part_csv_data(part_id)
			if not part_csv_data:
				print(f'[E] Could not get part data for ID: {part_id}. Aborting.')
				continue

			print(json.dumps(part_csv_data, indent=4))

PORT = 9581
pa: PartsboxAPI = None # type: ignore

def main() -> int:
	global pa
	apikey = os.environ['PARTSBOX_API_KEY']
	if not apikey:
		raise Exception('PARTSBOX_API_KEY not set in environment')
	pa = PartsboxAPI(apikey)

	print('Starting server')
	httpd = HTTPServer(('127.0.0.1', PORT), PartsboxPrinterReqHandler)
	print(f'Hosting server on port {PORT}')
	httpd.serve_forever()


if __name__ == '__main__':
	exit(main())