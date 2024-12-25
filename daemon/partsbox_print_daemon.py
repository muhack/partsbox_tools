#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import configparser
import os
import json
import re
import subprocess
import tempfile
from functools import reduce
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import TypeAlias

import requests

GLABELS_BIN = 'glabels-3-batch'
LPR_BIN = 'lpr'

class Part:
	'''
	Class to represent a part
	'''
	def __init__(self, url: str, part_id: str = ''):
		if url == '' and part_id == '' or url != '' and part_id != '':
			raise ValueError('Either URL or ID must be provided')
		if url == '':
			self.url: str = PartsboxAPI.get_IdAnything_url(part_id)
			self.part_id: str = part_id
		elif part_id == '':
			self.url: str = url
			self.part_id: str = self.get_part_id()
		self.part_data: dict = pa.get_part_data(self.part_id)

	def get_part_id(self) -> str:
		'''
		Get the part ID from a URL
		'''
		regex = r'partsbox.com\/.+?\/parts\/(\w{26})$'
		m = re.search(regex, self.url)
		if m:
			return m.group(1)
		raise ValueError(f'Could not get part ID from URL: {self.url}')

	def get_part_storage_id(self) -> str:
		'''
		Get the storage ID from part data
		'''
		return self.part_data.get('part/stock', [{}])[0].get('stock/storage-id', '')

	def get_part_total_stock(self) -> int:
		'''
		Get the total stock of a part across all storage locations
		'''
		return reduce(lambda x, y: x + y.get('stock/quantity'), self.part_data.get('part/stock', []), 0)

	def get_csv_data(self) -> dict:
		'''
		Get data for a part like the CSV you can download from the website
		Keys: Name, Description, Footprint, Manufacturer, MPN, Storage, Total Stock, URL, Meta-Parts
		NOTE: Meta-Parts is not easily available through the API, it seems
		'''

		part_data = pa.get_part_data(self.part_id)
		if not part_data:
			raise ValueError(f'Could not get part data for ID: {self.part_id}')
		storage_id = self.get_part_storage_id()
		storage_name = ''
		if storage_id:
			storage = Storage(storage_id=storage_id)
			storage_name = storage.get_storage_name()

		return {
			'Name': part_data.get('part/name', ''),
			'Description': part_data.get('part/description', ''),
			'Footprint': part_data.get('part/footprint', ''),
			'Manufacturer': part_data.get('part/manufacturer', ''),
			'MPN': part_data.get('part/mpn', ''),
			'Storage': storage_name,
			'Total Stock': self.get_part_total_stock(),
			'URL': PartsboxAPI.get_IdAnything_url(self.part_id),
			'Meta-Parts': '', # Sorry, no easy way to get this data with the API, it seems...
		}
	
	@property
	def template_path(self) -> str:
		'''
		Get the path to the glabels template for parts
		'''
		template_file = config.get('DEFAULT', 'GLABELS_PART_TEMPLATE')
		template_path = Path.cwd() / 'templates' / template_file
		return template_path.as_posix()

class Storage:
	'''
	Class to represent a storage location
	'''
	def __init__(self, url: str = '', storage_id: str = ''):
		if url == '' and storage_id == '' or url != '' and storage_id != '':
			raise ValueError('Either URL or ID must be provided')
		if url == '':
			self.url = PartsboxAPI.get_IdAnything_url(storage_id)
			self.storage_id = storage_id
		elif storage_id == '':
			self.url = url
			self.storage_id = self.get_storage_id()
		self.storage_data: dict = pa.get_storage_data(self.storage_id)

	def get_storage_id(self) -> str:
		'''
		Get the storage ID from a URL
		'''
		regex = r'partsbox.com\/.+?\/location\/(\w{26})$'
		m = re.search(regex, self.url)
		if m:
			return m.group(1)
		raise ValueError(f'Could not get storage ID from URL: {self.url}')

	def get_csv_data(self) -> dict:
		'''
		Get data for a storage location
		Keys: Name, Shortname, URL
		NOTE: Shortname is the part of the name after the last hyphen
		'''

		return {
			'Name': self.get_storage_name(),
			'Shortname': self.get_storage_name().split('-')[-1],
			'URL': PartsboxAPI.get_IdAnything_url(self.storage_id),
		}

	def get_storage_name(self) -> str:
		'''
		Get the name of a storage location
		'''
		return self.storage_data.get('storage/name', '')
	
	@property
	def template_path(self) -> str:
		'''
		Get the path to the glabels template for storage locations
		'''
		template_file = config.get('DEFAULT', 'GLABELS_STORAGE_TEMPLATE')
		template_path = Path.cwd() / 'templates' / template_file
		return template_path.as_posix()

Entity: TypeAlias = Part|Storage

class PartsboxAPI:
	'''
	Class to interact with the Partsbox API
	'''
	@staticmethod
	def get_IdAnything_url(id: str) -> str:
		'''
		Get the IDAnything URL for a part, location, etc.
		'''
		return f'https://partsbox.com/I{id}'

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

		# Parse the JSON data and prepare the response
		response = {}
		data_decoded = json.loads(data.decode('utf-8'))
		if not isinstance(data_decoded, list):
			print(f'[E] Expected a list of urls, got {type(data_decoded)} ({data_decoded:20}...)')
			response['status'] = 'Not Acceptable'
			response['message'] = 'Expected a list of URLs'
			self.send_dict_response(response)
			return
		response['status'] = 'OK'
		self.send_dict_response(response)

		parts_csv_data = process_urls(data_decoded)
		print_data(parts_csv_data)

def process_urls(urls: list[str]) -> list[Entity]:
	'''
	Process a list of URLs and returns a list of dictionaries with data
	that can be consumed by the glabels templates.
	Links must be all of the same type (for glabels to work)
	'''
	entities: list[Part|Storage] = []
	for url in urls:
		print(f'[D] Processing URL: {url}')

		entity: Part|Storage = None # type: ignore
		if '/parts/' in url:
			entity = Part(url)
		elif '/location/' in url:
			entity = Storage(url)
		else:
			raise ValueError(f'URL is neither a part nor a storage location ({url})')
		entities.append(entity)
	
	return entities

def print_data(entities: list[Entity]):
	'''
	Generate a label and print it

	:param param_data: Entities to print (must be all of the same type)
	:param printer_name: Name of the printer to use (defaults to system default printer)
	'''
	if not entities:
		print('[E] No data to print')
		return
	if not all(isinstance(entity, type(entities[0])) for entity in entities):
		raise ValueError('All entities must be of the same type')
	
	parts_data = [entity.get_csv_data() for entity in entities]
	template_file = entities[0].template_path

	# Create a temporary file to store the data
	with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
		print(f'[D] Writing data to {f.name}')
		f.write(','.join(list(map(lambda x: f"\"{x}\"", parts_data[0].keys()))))
		for part_data in parts_data:
			f.write('\n')
			f.write(','.join(list(map(lambda x: f"\"{x}\"", part_data.values()))))
		f.flush()

		# Generate the labels
		print(f'[D] Generating labels to {f.name}.pdf')
		glabels_args = [template_file, '-i', f.name, '-o', f'{f.name}.pdf']
		try:
			subprocess.run([GLABELS_BIN] + glabels_args, check=True, text=True, capture_output=True, timeout=10)
		except subprocess.CalledProcessError as e:
			print(f'[E] Could not generate labels: {e.stdout}, {e.stderr}')
			return

		if args.dry_run:
			# Open the PDF in a viewer
			print('[D] Opening PDF in viewer')
			try:
				subprocess.run(['xdg-open', f'{f.name}.pdf'], check=True)
			except subprocess.CalledProcessError as e:
				print(f'[E] Could not open PDF in viewer: {e.stdout}, {e.stderr}')
				return
			input('Press Enter when done...')
		else:
			# Print the labels
			print('[D] Printing labels')
			printer_name = config.get('DEFAULT', 'LPR_PRINTER')
			if printer_name is None:
				lpr_args = [f'{f.name}.pdf']
			else:
				lpr_args = ['-P', printer_name, f'{f.name}.pdf']
			try:
				subprocess.run([LPR_BIN] + lpr_args, check=True, text=True, capture_output=True)
			except subprocess.CalledProcessError as e:
				print(f'[E] Could not print labels: {e.stdout}, {e.stderr}')
				return

		# Clean up
		print('[D] Done, cleaning up')
		os.remove(f'{f.name}.pdf')
		os.remove(f.name)

pa: PartsboxAPI = None # type: ignore
config: configparser.ConfigParser = None # type: ignore
args: argparse.Namespace = None # type: ignore

def parse_args():
	parser = argparse.ArgumentParser(description='Partsbox Print Daemon')
	parser.add_argument('config', type=str, help='Path to the configuration file')
	parser.add_argument('--dry-run', action='store_true', help='Run the daemon in dry-run mode (open resulting PDFs in viewer)')
	return parser.parse_args()

def load_config(config_path):
	config = configparser.ConfigParser()
	config.read(config_path)
	return config

def main():
	global pa
	global config
	global args

	args = parse_args()
	config = load_config(args.config)

	apikey = os.environ.get('PARTSBOX_API_KEY')
	if not apikey:
		raise OSError('PARTSBOX_API_KEY not set in environment')
	pa = PartsboxAPI(apikey)

	port = config.getint('DEFAULT', 'PORT', fallback=9581)
	print('Starting server')
	httpd = HTTPServer(('127.0.0.1', port), PartsboxPrinterReqHandler)
	print(f'Hosting server on port {port}')
	httpd.serve_forever()

if __name__ == '__main__':
	main()
