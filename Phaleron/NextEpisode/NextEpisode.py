#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

import json
from lxml import html
from urllib.request import build_opener
from urllib.error import URLError, HTTPError
from colorama import Fore, Back, Style
import os
from http.client import RemoteDisconnected


class NextEpisode(object):
	
	def __init__(self, parent=None):
		super(NextEpisode, self).__init__()
		
		self.parent = parent
		# print(os.getcwd())
		
		# Open showchecklist
		with open("ShowChecklist.txt", 'r') as file:
			self.CheckList = json.load(file)
			file.close()
		
		# Build URL downloader and disguise as Mozilla
		self.opener = build_opener()
		self.opener.addheaders = [("User-agent", "Mozilla/5.0 (X11; Linux x86_64)"),
								  ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"),
								  ("Accept_encoding", "gzip, deflate, br"),
								  ("Accept_language", "en-US,en;q=0.9"),
								  ("Upgrade_insecure_requests", "1")
								  ]
		self.title = ""
		self.error_flag = 0
		
		try:
			self.scrapetitle()

		except HTTPError as e:
			self.error_flag = 1
			print(Fore.LIGHTRED_EX + f"Page not found. 404.  {e}" + Style.RESET_ALL)

		except URLError as e:
			self.error_flag = 1
			print(Fore.LIGHTRED_EX + f"Please connect to the internet and try again. {e}" + Style.RESET_ALL)

		except RemoteDisconnected as e:
			self.error_flag = 1
			print(Fore.LIGHTRED_EX + f"Connection closed by server without response. {e}" + Style.RESET_ALL)


		if self.error_flag == 0:

			# for i in CheckList: print(i, CheckList[i])
			print("Saving...")
			with open("ShowChecklist.txt", 'w') as file:
				json.dump(self.CheckList, file, ensure_ascii=False)
				file.close()

		else:
			self.error_flag = 0
			print("Not Saving...")
			pass

	# Scrape title information and format appropriately
	def scrapetitle(self):
		
		for i in self.CheckList:

			if self.CheckList[i][2] == 1:
			
				# Show or Commic flag
				self.show = 1

				print("Webpage:", i)

				self.page = self.opener.open(i).read()

				self.root = html.fromstring(self.page)

				if 'watchcartoononline' in i or 'wcostream' in i:

					catList = self.root.get_element_by_id('catlist-listview')

					self.title = catList.text_content().split("    ")[1]

				elif 'mangapanda' in i:

					catList = self.root.get_element_by_id('latestchapters')

					self.title = catList.text_content().split("\n\n\n")[1].replace("\n", "").replace(":", "") + "\n"

					self.show = 0

				elif "watch-series" in i:

					catList = self.root.find(".//a[@class='videoHname']")

					self.title = catList.text_content().split(" " * 17)[1] + "\n"

				# elif 'swatchseries' in i:
				#

				# 	catList = self.root.find(".//div[@class='latest-episode']")
				#
				# 	self.title = f"{str(i.split('/')[-1]).title()} " + " ".join(" ".join(catList.text_content().split()).split("←♥→")[0].split()[2:]) + "\n"

				elif 'cmovies' in i:
					catList = self.root.find(".//li[@class='ep-item active']")
					titleList = i.split("/")[-2].split("-")
					for j in range(len(titleList)):
						titleList[j] = titleList[j].capitalize()


					self.title = " ".join(titleList) + " " + catList.text_content().strip() + "\n"

				if self.show == 1:
					self.checkshow(i, self.title)

				elif self.show == 0:
					self.checkmanga(i, self.title)


			
	def checkshow(self, url, title):
		
		season = 0
		newseason = False
		if "Season" in title:
			season = int(title[title.find("Season"):].split()[1])
		if title.lower().count("episode") > 1:
			episode = title[title.rfind('Episode'):].split()[1]
		else:
			episode = title[title.find('Episode'):].split()[1]

		if "." in episode:
			episode = float(episode)
		else:
			episode = int(episode)

		if season > 0:
			if season > int(self.CheckList[url][0]):
				newseason = True
				print(Fore.LIGHTRED_EX + Back.CYAN + "New Season:" + Style.RESET_ALL, end=" ")
				if episode < int(self.CheckList[url][0]):
					self.CheckList[url][1] = episode
		
		if episode > int(self.CheckList[url][1]) or newseason == True:
			self.CheckList[url] = [season, episode, self.CheckList[url][2]]
			print(Fore.LIGHTRED_EX + Back.CYAN + "New Episode:" + Style.RESET_ALL)
		
		print(title)
		
	def checkmanga(self, url, title):

		issue = int([chapter for chapter in title.split() if chapter.isdigit()][0])
		#issue = int(title.split()[1])

		if issue > int(self.CheckList[url][1]):
			self.CheckList[url][1] = issue
			print(Fore.LIGHTRED_EX + Back.BLUE + "New Issue:" + Style.RESET_ALL)
		
		print(title)
		
		
TVGuide = NextEpisode()
		