#!/usr/bin/python
# -*- coding: utf-8 -*-

# =============================================================================
#  Version: 1.0 (Aug 30, 2018)
#  Author: Eun-kyung Kim (kekeeo@kaist.ac.kr), KAIST, South Korea
# =============================================================================
#  Copyright (c) 2018. Eun-kyung Kim (kekeeo@kaist.ac.kr)
# =============================================================================

# Program version
version = '1.1'

# Configurations
# =============================================================================
#esbm_benchmark_path = './ESBM_benchmark/'

fca_lattice_path = './KAFCA_lattice/'
#kafca_final_result_path = './KAFCA_result/'
# =============================================================================

import re

uninformative_values = ['wikidata', 'Thing', 'Agent']


def extract_key_tokens(objects):
	re1 = '((?:[a-z][a-z]+))'  # Word
	re2 = '(\\d+)'  # Integer Number
	rg = re.compile(re1 + re2, re.IGNORECASE | re.DOTALL)

	rlt = set([])

	if '^^' not in objects:
		object_info_token = objects.split('/')[-1].split('#')[-1].replace('>', '').replace('_', ' ').replace(
			'Category:', '').replace('"@en', '').replace('"', '')
		if object_info_token.isdigit():
			try:
				object_info_token_ = objects.split('/')[-2].split('#')[-1].replace('>', '').replace('_', ' ').replace(
					'Category:', '').replace('"@en', '').replace('"', '')
			except IndexError:
				object_info_token_ = ''
			object_info_token = object_info_token_ + object_info_token

	else:
		object_info_token = objects.split('^^')[0].split('/')[-1].split('#')[-1].replace('>', '').replace('_',
																										  ' ').replace(
			'Category:', '').replace('"@en', '').replace('"', '')

	if 'http://' in objects:
		object_info_token = re.sub(r"(\w)([A-Z])", r"\1 \2", object_info_token)

	for word in object_info_token.lower().split():

		m = rg.search(word)
		if m:
			word_part = m.group(1)
			int_part = m.group(2)

			rlt.add(word_part)
		else:
			rlt.add(word)
	return rlt


from flask import Flask, request, jsonify

app = Flask (__name__)

@app.errorhandler(404)
def page_not_found(error):
	app.logger.error(error)
	return 'page_not_found'

@app.route('/')
def hello_world():
	return "Hello"

@app.route('/summary', methods = ['POST'])
def extract_sumz():
	import os
	import csv
	import copy
	print 'summary'
	input_json = request.get_json(force=True)
	#print input_json
	print type(input_json)
	input_entity = input_json['entity']
	input_KB = input_json['KB']

	target_entity = set([])
	target_entity.add(input_entity)

	if not os.path.isdir(fca_lattice_path):
		os.mkdir(fca_lattice_path)
	fcs_lattice_filename = fca_lattice_path + 'FCA_' + input_entity + '.csv'
	fcs_lattice_file = open(fcs_lattice_filename, 'w')

	sep = ':-:'

	property_set = set([])
	target_facts = set([])
	for row in input_KB:
		s = row.strip().split()[0]
		p = row.strip().split()[1]
		o = ' '.join(row.strip().split()[2:])[:-2]

		if s not in target_entity and o in target_entity:
			_s = s
			s = o + '[FALSE]'
			o = _s

		property_set.add(p)
		target_facts.add(s + sep + p + sep + o)
	property_list = list(property_set)
	property_list.insert(0, '')

	fca_csv = [property_list]

	final_rank = {}

	attribute_map = {}
	for spo in target_facts:
		default_score = 1
		s, p, o = spo.split(sep)
		s = s.replace('[FALSE]', '')

		# If there is less information available from the surface information, the score will be lower.
		for uninform_str in uninformative_values:
			if uninform_str in o:
				default_score = 0

		if default_score > 0:

			# building attribute-token dict
			try:
				attribute_map[p] = attribute_map[p] | extract_key_tokens(o)
			except KeyError:
				attribute_map[p] = extract_key_tokens(o)

		final_rank[s + sep + p + sep + o] = default_score

	for spo, v in sorted(final_rank.items(), key=lambda x: x[1], reverse=True):
		tmp_fca_list = [''] * len(property_list)

		s, p, o = spo.split(sep)
		tmp_fca_list[0] = p + sep + o
		tmp_fca_list[property_list.index(p)] = 'X'

		for prop, tokens in attribute_map.items():
			for token in tokens:
				if token in o.lower():
					tmp_fca_list[property_list.index(prop)] = 'X'

		# print tmp_fca_list
		fca_csv.append(tmp_fca_list)

	tmp_list = copy.deepcopy(fca_csv)
	with fcs_lattice_file:
		writer = csv.writer(fcs_lattice_file)
		for index, row in enumerate(fca_csv):
			for index_se, ele in enumerate(row):
				#print ele
				tmp_list[index][index_se] = ele.encode('utf-8')
		writer.writerows(tmp_list)

	# Formal concept analysis
	from concepts import Context
	#fcs_lattice_filename = './KAFCA_lattice/FCA_141.csv'
	c = Context.fromfile(fcs_lattice_filename, frmat='csv')
	hierarchical_layer = 0
	for extents, intents in c.lattice:
		#print extents, intents
		#f = open('text2.json', 'w')
		#json.dump(final_rank, f, ensure_ascii=False, indent=4)
		for extent in extents:
			try:
				extent_de = extent.decode('utf-8')
				if final_rank[s+sep+extent_de] == 1:
					final_rank[s+sep+extent_de] = len(target_facts) - hierarchical_layer
			except KeyError:
				print s+sep+extent_de
				continue

		hierarchical_layer += 1
	#print '-'*10
	#print final_rank.keys()

	os.remove(fcs_lattice_filename)
	result_top5 = []
	chkcount = 0
	for spo, score in sorted(final_rank.items(), key=lambda x: x[1], reverse=True):
		s, p, o = spo.split(sep)

		if spo not in target_facts:
			_s = s
			s = o
			o = _s
		chkcount += 1

		result_top5.append(s+'\t'+p+'\t'+o)

		if chkcount == 5:
			break

	result = {}
	result['top5'] = result_top5

	return jsonify(result)



'''
def main():
	import os
	import sys
	import csv

	if not os.path.isdir(esbm_benchmark_path):
		print 'The esbm benchmark directory is required.'
		sys.exit(1)

	given_entities = esbm_benchmark_path + 'elist.txt'
	target_entities = set([])
	for row in open(given_entities):
		target_entities.add('<' + row.strip().split('\t')[2] + '>')

	for entity_idx in range(1, 142):

		if entity_idx > 140:
			targetKB = 'kbox'
			print 'on'
		elif entity_idx > 100:
			targetKB = 'lmdb'
		else:
			targetKB = 'dbpedia'

		# One given entity description file
		entity_decriptions = esbm_benchmark_path + targetKB + '/' + str(entity_idx) + '/' + str(entity_idx) + '_desc.nt'

		# Creating a grid of formal concepts and save it as a CSV file
		if not os.path.isdir(fca_lattice_path):
			os.mkdir(fca_lattice_path)
		fcs_lattice_filename = fca_lattice_path + 'FCA_' + str(entity_idx) + '.csv'
		fcs_lattice_file = open(fcs_lattice_filename, 'w')

		sep = ':-:'

		property_set = set([])
		target_facts = set([])
		for row in open(entity_decriptions, 'r'):
			s = row.strip().split()[0]
			p = row.strip().split()[1]
			o = ' '.join(row.strip().split()[2:])[:-2]

			if s not in target_entities and o in target_entities:
				_s = s
				s = o + '[FALSE]'
				o = _s

			property_set.add(p)
			target_facts.add(s + sep + p + sep + o)
		property_list = list(property_set)
		property_list.insert(0, '')

		fca_csv = [property_list]

		final_rank = {}

		attribute_map = {}
		for spo in target_facts:
			default_score = 1
			s, p, o = spo.split(sep)
			s = s.replace('[FALSE]', '')

			# If there is less information available from the surface information, the score will be lower.
			for uninform_str in uninformative_values:
				if uninform_str in o:
					default_score = 0

			if default_score > 0:

				# building attribute-token dict
				try:
					attribute_map[p] = attribute_map[p] | extract_key_tokens(o)
				except KeyError:
					attribute_map[p] = extract_key_tokens(o)

			final_rank[s + sep + p + sep + o] = default_score

		for spo, v in sorted(final_rank.items(), key=lambda x: x[1], reverse=True):
			tmp_fca_list = [''] * len(property_list)

			s, p, o = spo.split(sep)
			tmp_fca_list[0] = p + sep + o
			tmp_fca_list[property_list.index(p)] = 'X'

			for prop, tokens in attribute_map.items():
				for token in tokens:
					if token in o.lower():
						tmp_fca_list[property_list.index(prop)] = 'X'

			# print tmp_fca_list
			fca_csv.append(tmp_fca_list)

		with fcs_lattice_file:
			writer = csv.writer(fcs_lattice_file)
			writer.writerows(fca_csv)

		# Formal concept analysis
		from concepts import Context
		c = Context.fromfile(fcs_lattice_filename, frmat='csv')
		hierarchical_layer = 0
		for extents, intents in c.lattice:
			# print extents, intents
			for extent in extents:

				if final_rank[s + sep + extent] == 1:
					final_rank[s + sep + extent] = len(target_facts) - hierarchical_layer

			hierarchical_layer += 1

		# Generating result file
		if not os.path.isdir(kafca_final_result_path):
			os.mkdir(kafca_final_result_path)

		if not os.path.isdir(kafca_final_result_path + targetKB):
			os.mkdir(kafca_final_result_path + targetKB)

		output_filepath = kafca_final_result_path + targetKB + '/' + str(entity_idx) + '/'
		if not os.path.isdir(output_filepath):
			os.mkdir(output_filepath)

		fo_top5 = open(output_filepath + str(entity_idx) + '_top5.nt', 'wb')
		fo_top10 = open(output_filepath + str(entity_idx) + '_top10.nt', 'wb')
		fo_rank = open(output_filepath + str(entity_idx) + '_rank.nt', 'wb')

		chkcount = 0
		for spo, score in sorted(final_rank.items(), key=lambda x: x[1], reverse=True):
			s, p, o = spo.split(sep)

			if spo not in target_facts:
				_s = s
				s = o
				o = _s
			chkcount += 1

			try:
				fo_rank.write("%s %s %s .\n" % (s, p, o))
				fo_top10.write("%s %s %s .\n" % (s, p, o))
				fo_top5.write("%s %s %s .\n" % (s, p, o))
			except ValueError:
				pass

			if chkcount == 5:
				fo_top5.close()

			if chkcount == 10:
				fo_top10.close()

		fo_rank.close()
'''

if __name__ == '__main__':
	#main()
	tmp_KB = []
	''' test
	for row in open('./ESBM_benchmark/kbox/141/141_desc.nt', 'rb'):
		tmp_KB.append(row.split()[0]+' '+row.split()[1]+' '+row.split()[2]+' '+row.split()[3])
	print len(tmp_KB)
	print extract_sumz(tmp_KB, '<애플_(기업)>') 
	'''
	app.run(debug=True, host='0.0.0.0', port=5000)
	#app.run(debug=True, host="143.248.136.214", port=5000)
