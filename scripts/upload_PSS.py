#encoding: utf-8
import codecs
import re
import os.path
from indic_transliteration import sanscript
from indic_transliteration.sanscript import SchemeMap, SCHEMES, transliterate
from vernacular import vernacular
from internetarchive import get_item, upload, modify_metadata
import datetime
import time
import json
import glob
import sys

	
# Convert the text into various transliteration schemes.
def trans(text, inputScheme=sanscript.DEVANAGARI):
	hk = transliterate(text, inputScheme, sanscript.HK)
	slp1 = transliterate(text, inputScheme, sanscript.SLP1)
	itrans = transliterate(text, inputScheme, sanscript.ITRANS)
	iast = transliterate(text, inputScheme, sanscript.IAST)
	kolkata = transliterate(text, inputScheme, sanscript.KOLKATA)
	velthuis = transliterate(text, inputScheme, sanscript.VELTHUIS)
	bengali = transliterate(text, inputScheme, sanscript.BENGALI)
	devanagari = transliterate(text, inputScheme, sanscript.DEVANAGARI)
	gujarati = transliterate(text, inputScheme, sanscript.GUJARATI)
	gurmukhi = transliterate(text, inputScheme, sanscript.GURMUKHI)
	kannada = transliterate(text, inputScheme, sanscript.KANNADA)
	malayalam = transliterate(text, inputScheme, sanscript.MALAYALAM)
	oriya = transliterate(text, inputScheme, sanscript.ORIYA)
	tamil = transliterate(text, inputScheme, sanscript.TAMIL)
	telugu = transliterate(text, inputScheme, sanscript.TELUGU)
	optitrans = transliterate(text, inputScheme, sanscript.OPTITRANS)
	keyword = vernacular(itrans)
	
	return {'devanagari':devanagari, 'hk':hk, 'slp1':slp1, 'itrans':itrans, 'iast':iast, 'kolkata':kolkata, 'velthuis':velthuis, 'optitrans':optitrans,
	'bengali':bengali, 'gujarati':gujarati, 'kannada':kannada, 'malayalam':malayalam, 'oriya':oriya, 'tamil':tamil, 'telugu':telugu, 'keyword':keyword}

def padAccessionNumber(accession):
	number = re.sub('[a-zA-Z]*$', '', accession)
	number1 = '0'*(4-len(number)) + number
	accession = accession.replace(number, number1)
	accession = accession.upper()
	accession = re.sub('([A-Z])$', '-\g<1>', accession)
	return accession

# Createa a metadata dict from each line of Catalogue. Catalogue has total 16 fields. They are read into dict details, and further processed. 68 entries produced to upload to archive.org.
def find_metadata(line):
	details = line.rstrip('\r\n').split('\t')
	metadata = {}
	if not len(details) == 17:
		print(details[0] + ' does not have 17 fields. Please check.')
	# Get metadata from CSV
	metadata['Sr_No'] = details[0]
	# Exercise to prepare a pad around the accession number e.g. 24 -> 0024. Also convert a,b etc to -A,-B etc e.g. 424a -> 0424-A
	accession = str(details[1])
	accession = padAccessionNumber(accession)
	metadata['Accession_No'] = accession
	# Convert title to various transliterations
	for (key, item) in trans(details[2]).items():
		metadata['Title_'+key] = item
	# Convert author to various transliterations
	for (key, item) in trans(details[3]).items():
		metadata['Author_'+key] = item
	# Convert commentator to various transliterations
	for (key, item) in trans(details[4]).items():
		metadata['Commentator_'+key] = item
	metadata['Material'] = details[5]
	metadata['Script'] = details[6]
	metadata['aSize'] = details[7]
	metadata['bSize'] = details[8]
	metadata['Line'] = details[9]
	metadata['Letters'] = details[10]
	metadata['Folios'] = details[11]
	for (key, item) in trans(details[12]).items():
		metadata['Scribe_'+key] = item
	metadata['Condition'] = details[13]
	metadata['Age_of_MS'] = details[14]
	metadata['Additional_remarks'] = details[15]
	metadata['Subject'] = details[16]
	# Prepare mandatory metadata for Archive.org.
	titlekey = str(metadata['Title_keyword'])
	titlekey = re.sub('[^a-zA-Z0-9_. -]', ' ', titlekey) # See issue 12.
	titlekey = re.sub('[ ]+', '_', titlekey)
	titlekey = re.sub('^[_.-]+', '', titlekey) # See issue 13.
	identifier = titlekey+'-CGV-PSS-'+metadata['Sr_No']+'-'+metadata['Accession_No']
	identifier = re.sub('[^a-zA-Z0-9_. -]', '_', identifier)
	metadata['identifier'] = identifier
	metadata['mediatype'] = 'texts'
	metadata['collection'] = 'opensource'
	metadata['creator'] = 'Chunilal Gandhi Vidyabhavan Surat'
	metadata['description'] = 'Pandit Shivadatta Shukla collection of manuscripts of Chunilal Gandhi Vidyabhavan, Surat.'
	metadata['language'] = 'san'
	metadata['email'] = 'cgvidyabhavan@gmail.com'
	return metadata


def uploadToArchive(metadata):
	identifier = metadata['identifier']
	flog = codecs.open('../logs/uploadLog.txt', 'a', 'utf-8')
	if len(identifier) > 100:
		print('File name too long: ' + identifier)
		flog.write('File name too long: ' + identifier + '\n----------\n')
	else:
		accession = metadata['Accession_No']
		sr = metadata['Sr_No']
		startMessage = sr+'#'+accession+'#'+identifier+'\n'+'Started at '+str(datetime.datetime.now())
		print(startMessage)
		flog.write(startMessage+'\n')
		r = upload(identifier, {identifier+'.pdf': '../../ChunilalGandhiMSS/compressedPdfFiles/BOOK_NO.'+accession+'.pdf'}, metadata=metadata)
		endMessage=str(r[0].status_code)+'\n'+'Ended at '+str(datetime.datetime.now())+'\n----------\n'
		print(endMessage)
		flog.write(endMessage)
		flog.close()
	
def createMetadataJson():
	fin = codecs.open('../derivedFiles/new3.tsv', 'r', 'utf-8')
	ferror = codecs.open('../logs/error.txt', 'a', 'utf-8')
	print('Files not found')
	for line in fin:
		metadata = find_metadata(line)
		identifier = metadata['identifier']
		accession = metadata['Accession_No']
		sr = metadata['Sr_No']
		if not os.path.isfile('../../ChunilalGandhiMSS/compressedPdfFiles/BOOK_NO.'+accession+'.pdf'):
			ferror.write('File Not Found:'+accession+'\n')
			print(accession)
		else:
			with codecs.open('../metadataJson/'+accession+'.json', 'w', 'utf-8') as fjson:
				json.dump(metadata, fjson)
				#print('Metadata generated for:'+accession)

	fin.close()
	ferror.close()


if __name__=="__main__":
	if len(sys.argv) > 1:
		createMetadataJson()
	
	accessionsToBeUploaded = '../derivedFiles/uploadstack.txt'
	for line in codecs.open(accessionsToBeUploaded, 'r', 'utf-8'):
		accession = line.rstrip()
		accession = padAccessionNumber(accession)
		if os.path.isfile('../metadataJson/'+accession+'.json'):
			metadata = json.load(codecs.open('../metadataJson/'+accession+'.json', 'r', 'utf-8'))
			uploadToArchive(metadata)
		else:
			print('FILE NOT FOUND: '+accession)
