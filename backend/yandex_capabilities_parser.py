#!/usr/bin/env python3
"""
Парсер для сбора capabilities устройств с сайта Яндекса Smart Home
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from typing import Dict, List, Any
from urllib.parse import urljoin
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YandexCapabilitiesParser:
    def __init__(self):
        self.base_url = "https://yandex.ru/dev/dialogs/smart-home/doc/en/concepts/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Маппинг типов устройств на URL страниц
        self.device_type_mapping = {
            'devices.types.sensor': 'device-type-sensor',
            'devices.types.sensor.button': 'device-type-sensor-button',
            'devices.types.sensor.climate': 'device-type-sensor-climate',
            'devices.types.sensor.gas': 'device-type-sensor-gas',
            'devices.types.sensor.illumination': 'device-type-sensor-illumination',
            'devices.types.sensor.motion': 'device-type-sensor-motion',
            'devices.types.sensor.open': 'device-type-sensor-open',
            'devices.types.sensor.smoke': 'device-type-sensor-smoke',
            'devices.types.sensor.vibration': 'device-type-sensor-vibration',
            'devices.types.sensor.water_leak': 'device-type-sensor-water-leak',
            'devices.types.smart_meter': 'device-type-smart-meter',
            'devices.types.smart_meter.cold_water': 'device-type-smart-meter-cold-water',
            'devices.types.smart_meter.electricity': 'device-type-smart-meter-electricity',
            'devices.types.smart_meter.gas': 'device-type-smart-meter-gas',
            'devices.types.smart_meter.heat': 'device-type-smart-meter-heat',
            'devices.types.smart_meter.hot_water': 'device-type-smart-meter-hot-water',
            'devices.types.camera': 'device-type-camera',
            'devices.types.media_device': 'device-type-media-device',
            'devices.types.media_device.receiver': 'device-type-media-device-receiver',
            'devices.types.media_device.tv': 'device-type-media-tv',
            'devices.types.media_device.tv_box': 'device-type-media-device-tv-box',
            'devices.types.cooking': 'device-type-cooking',
            'devices.types.cooking.coffee_maker': 'device-type-cooking-coffee-maker',
            'devices.types.cooking.kettle': 'device-type-cooking-kettle',
            'devices.types.cooking.multicooker': 'device-type-cooking-multicooker',
            'devices.types.dishwasher': 'device-type-dishwasher',
            'devices.types.iron': 'device-type-iron',
            'devices.types.vacuum_cleaner': 'device-type-vacuum-cleaner',
            'devices.types.washing_machine': 'device-type-washing-machine',
            'devices.types.pet_drinking_fountain': 'device-type-pet-drinking-fountain',
            'devices.types.pet_feeder': 'device-type-pet-feeder',
            'devices.types.humidifier': 'device-type-humidifier',
            'devices.types.purifier': 'device-type-purifier',
            'devices.types.thermostat': 'device-type-thermostat',
            'devices.types.thermostat.ac': 'device-type-thermostat-ac',
            'devices.types.ventilation': 'device-type-ventilation',
            'devices.types.ventilation.fan': 'device-type-ventilation-fan',
            'devices.types.light': 'device-type-light',
            'devices.types.light.lamp': 'device-type-light-lamp',
            'devices.types.light.ceiling': 'device-type-light-ceiling',
            'devices.types.light.strip': 'device-type-light-strip',
            'devices.types.socket': 'device-type-socket',
            'devices.types.switch': 'device-type-switch',
            'devices.types.switch.relay': 'device-type-switch-relay',
            'devices.types.openable': 'device-type-openable',
            'devices.types.openable.curtain': 'device-type-openable-curtain',
            'devices.types.openable.valve': 'device-type-openable-valve',
            'devices.types.other': 'device-type-other'
        }

    def parse_capabilities_from_page(self, device_type: str) -> Dict[str, Any]:
        """Парсит capabilities с страницы конкретного типа устройства"""
        url_suffix = self.device_type_mapping.get(device_type)
        if not url_suffix:
            logger.warning(f"Не найден URL для типа устройства: {device_type}")
            return {"capabilities": [], "properties": []}
        
        url = urljoin(self.base_url, url_suffix)
        logger.info(f"Парсинг {device_type} с URL: {url}")
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем секцию с Recommended capabilities
            capabilities_section = None
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                if 'capabilities' in heading.get_text().lower():
                    capabilities_section = heading
                    break
            
            if not capabilities_section:
                logger.warning(f"Не найдена секция capabilities для {device_type}")
                return {"capabilities": [], "properties": []}
            
            # Ищем таблицу с capabilities
            table = capabilities_section.find_next('table')
            if not table:
                logger.warning(f"Не найдена таблица capabilities для {device_type}")
                return {"capabilities": [], "properties": []}
            
            capabilities = []
            properties = []
            
            # Парсим строки таблицы
            rows = table.find_all('tr')[1:]  # Пропускаем заголовок
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    capability_cell = cells[0].get_text().strip()
                    instances_cell = cells[1].get_text().strip()
                    
                    # Извлекаем capability
                    if 'devices.capabilities.' in capability_cell:
                        capability = capability_cell.split('devices.capabilities.')[-1].split()[0]
                        
                        # Парсим instances и values
                        instances_values = self._parse_instances_values(instances_cell)
                        
                        capabilities.append({
                            "type": f"devices.capabilities.{capability}",
                            "instances": instances_values
                        })
                    
                    # Проверяем properties
                    elif 'devices.properties.' in capability_cell:
                        property_name = capability_cell.split('devices.properties.')[-1].split()[0]
                        properties.append(f"devices.properties.{property_name}")
            
            logger.info(f"Найдено {len(capabilities)} capabilities и {len(properties)} properties для {device_type}")
            return {"capabilities": capabilities, "properties": properties}
            
        except requests.RequestException as e:
            logger.error(f"Ошибка при запросе {url}: {e}")
            return {"capabilities": [], "properties": []}
        except Exception as e:
            logger.error(f"Ошибка при парсинге {device_type}: {e}")
            return {"capabilities": [], "properties": []}

    def _parse_instances_values(self, instances_text: str) -> List[Dict[str, Any]]:
        """Парсит instances и values из текста"""
        instances = []
        
        # Ищем Function: и Values:
        function_match = re.search(r'Function:\s*([^.]+)', instances_text)
        values_match = re.search(r'Values:\s*([^.]+)', instances_text)
        
        if function_match:
            function = function_match.group(1).strip()
            values = []
            
            if values_match:
                values_text = values_match.group(1).strip()
                if values_text.lower() != 'not supported':
                    # Парсим значения, разделенные запятыми
                    values = [v.strip() for v in values_text.split(',') if v.strip()]
            
            instances.append({
                "function": function,
                "values": values
            })
        
        return instances

    def parse_all_device_types(self, device_types: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Парсит capabilities для всех типов устройств"""
        results = {}
        
        for device_type_info in device_types:
            device_type = device_type_info['type']
            logger.info(f"Обработка {device_type}...")
            
            capabilities_data = self.parse_capabilities_from_page(device_type)
            results[device_type] = capabilities_data
            
            # Небольшая задержка между запросами
            time.sleep(1)
        
        return results

    def update_device_types_file(self, input_file: str, output_file: str = None):
        """Обновляет файл с типами устройств новыми capabilities"""
        if output_file is None:
            output_file = input_file
        
        # Загружаем существующие типы устройств
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        device_types = data['types']
        
        # Парсим capabilities для всех типов
        capabilities_results = self.parse_all_device_types(device_types)
        
        # Обновляем данные
        for device_type_info in device_types:
            device_type = device_type_info['type']
            if device_type in capabilities_results:
                result = capabilities_results[device_type]
                
                # Обновляем capabilities
                if result['capabilities']:
                    device_type_info['capabilities'] = result['capabilities']
                
                # Обновляем properties
                if result['properties']:
                    device_type_info['properties'] = result['properties']
                
                logger.info(f"Обновлен {device_type}: {len(result['capabilities'])} capabilities, {len(result['properties'])} properties")
        
        # Сохраняем обновленный файл
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Файл обновлен: {output_file}")

def main():
    """Основная функция для запуска парсера"""
    parser = YandexCapabilitiesParser()
    
    # Путь к файлу с типами устройств
    input_file = "app/data/yandex_device_types.json"
    
    try:
        parser.update_device_types_file(input_file)
        print("Парсинг завершен успешно!")
    except Exception as e:
        logger.error(f"Ошибка при выполнении парсинга: {e}")

if __name__ == "__main__":
    main()
