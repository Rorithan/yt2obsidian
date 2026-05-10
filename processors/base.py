#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from pathlib import Path
from utils import safe_filename
from config import Config


class ContentProcessor(ABC):
    def __init__(self, url: str):
        self.url = url.strip()
        Config.ensure_dirs()

    @abstractmethod
    def process(self) -> Path:
        pass

    def _get_safe_filename(self, title: str) -> str:
        return safe_filename(title)