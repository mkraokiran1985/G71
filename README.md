Пару слов  - как это все шевелится:
 работа основана на remap( поэтому немного проще действовать,если remap
 уже настроен в системе).
Еще желателен Qсad , по двум причинам: он работает под линукс(бесплатен) и проверен 
для "нашей" работы)).
установка:
sudo apt-get install qcad
версия значения не имеет,так как наворотов нам не требуется(да и нет их в qcad)))
========================
Для чертежа используем отрезки и дуги(окружности), скругления. 
получили файл .dxf
=============================
Далее наш файл .dxf открываем в емс,
в котором настроен фильтр на то,чтоб dxf открывала программка dxf2gcode.
В ней меняем настройки обработки(из основных: глубина съема за один проход,припуск на чистовую
обработку)
-------------------------------------------------------------------------------------
 remap должен быть "настроен" 
----------------------------------------------
папки dxf2gcode_v01 и dxf2gcode положить в папку с конфигом
( в принципе - без разницы ,если подправить пути)
---------------------
"основной " код  в файле remap.py
если он есть и задействован реально ,то нужно дополнить его кодом из "моего" файла remap.py,
а если не задействован,то его можно и заменить полностью на "мой"
------------------
Try the config  G71_sim_config
=========================================






























