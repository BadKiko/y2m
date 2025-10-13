#!/usr/bin/env python3
"""
Скрипт для очистки и нормализации capabilities в файле yandex_device_types.json
"""

import json
import re
from typing import Dict, List, Any

def clean_capabilities_data(input_file: str, output_file: str = None):
    """Очищает и нормализует данные capabilities"""
    if output_file is None:
        output_file = input_file
    
    # Загружаем данные
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    device_types = data['types']
    
    for device_type_info in device_types:
        device_type = device_type_info['type']
        
        # Очищаем capabilities
        if 'capabilities' in device_type_info:
            cleaned_capabilities = []
            
            for cap in device_type_info['capabilities']:
                if isinstance(cap, dict) and 'type' in cap:
                    # Очищаем instances
                    cleaned_instances = []
                    
                    if 'instances' in cap and isinstance(cap['instances'], list):
                        for instance in cap['instances']:
                            if isinstance(instance, dict) and 'function' in instance:
                                # Очищаем function от лишнего текста
                                function = instance['function']
                                if '\n' in function:
                                    function = function.split('\n')[0].strip()
                                
                                # Очищаем values
                                values = []
                                if 'values' in instance and isinstance(instance['values'], list):
                                    for value in instance['values']:
                                        if isinstance(value, str) and value.strip():
                                            values.append(value.strip())
                                
                                cleaned_instances.append({
                                    "function": function,
                                    "values": values
                                })
                    
                    cleaned_capabilities.append({
                        "type": cap['type'],
                        "instances": cleaned_instances
                    })
            
            device_type_info['capabilities'] = cleaned_capabilities
        
        # Очищаем properties (убираем дубликаты)
        if 'properties' in device_type_info:
            unique_properties = list(set(device_type_info['properties']))
            device_type_info['properties'] = unique_properties
    
    # Сохраняем очищенные данные
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Данные очищены и сохранены в {output_file}")

def print_capabilities_summary(input_file: str):
    """Выводит сводку по capabilities для всех устройств"""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    device_types = data['types']
    
    print("=== СВОДКА ПО CAPABILITIES ===\n")
    
    for device_type_info in device_types:
        device_type = device_type_info['type']
        name = device_type_info['name']
        
        capabilities_count = len(device_type_info.get('capabilities', []))
        properties_count = len(device_type_info.get('properties', []))
        
        print(f"{name} ({device_type}):")
        print(f"  Capabilities: {capabilities_count}")
        print(f"  Properties: {properties_count}")
        
        if capabilities_count > 0:
            for cap in device_type_info['capabilities']:
                cap_type = cap['type'].split('.')[-1]
                instances_count = len(cap.get('instances', []))
                print(f"    - {cap_type} ({instances_count} instances)")
        
        print()

def main():
    input_file = "app/data/yandex_device_types.json"
    
    print("Очистка данных capabilities...")
    clean_capabilities_data(input_file)
    
    print("\nСводка по capabilities:")
    print_capabilities_summary(input_file)

if __name__ == "__main__":
    main()
