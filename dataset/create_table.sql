CREATE TABLE IF NOT EXISTS Digimon(
  digimon_name TEXT,
  stage TEXT,
  digimon_type TEXT,
  attribute TEXT,
  memory INTEGER,
  equip_slots INTEGER,
  hp_lvl_1 INTEGER,
  sp_lvl_1 INTEGER,
  atk_lvl_1 INTEGER,
  def_lvl_1 INTEGER,
  int_lvl_1 INTEGER,
  spd_lvl_1 INTEGER,
  hp_lvl_50 INTEGER,
  sp_lvl_50 INTEGER,
  atk_lvl_50 INTEGER,
  def_lvl_50 INTEGER,
  int_lvl_50 INTEGER,
  spd_lvl_50 INTEGER,
  hp_lvl_99 INTEGER,
  sp_lvl_99 INTEGER,
  atk_lvl_99 INTEGER,
  def_lvl_99 INTEGER,
  int_lvl_99 INTEGER,
  spd_lvl_99 INTEGER,
  PRIMARY KEY (digimon_name)
);

CREATE TABLE IF NOT EXISTS Digivolution_Requirements(
  digimon_name TEXT,
  digimon_level INTEGER,
  hp_req INTEGER,
  sp_req INTEGER,
  atk_req INTEGER,
  def_req INTEGER,
  int_req INTEGER,
  spd_req INTEGER,
  abi_req INTEGER,
  cam_req INTEGER,
  extra_condition TEXT,
  PRIMARY KEY (digimon_name),
  FOREIGN KEY (digimon_name) REFERENCES Digimon(digimon_name)
);

CREATE TABLE IF NOT EXISTS Digivolutions(
  digivolves_from TEXT,
  digivolves_to TEXT,
  PRIMARY KEY (digivolves_from, digivolves_to),
  FOREIGN KEY (digivolves_from) REFERENCES Digimon(digimon_name),
  FOREIGN KEY(digivolves_to) REFERENCES Digimon(digimon_name)
);

CREATE TABLE IF NOT EXISTS Skills_Info(
  skill TEXT,
  sp_cost TEXT,
  skill_type TEXT,
  power TEXT,
  attribute TEXT,
  inheritable TEXT,
  skill_description TEXT,
  PRIMARY KEY (skill)
);

CREATE TABLE IF NOT EXISTS Digimon_Skills(
  digimon_name TEXT,
  skill TEXT,
  digimon_level INTEGER,
  PRIMARY KEY (digimon_name, skill),
  FOREIGN KEY (digimon_name) REFERENCES Digimon(digimon_name),
  FOREIGN KEY (skill) REFERENCES Skills_Info(skill)
);

CREATE TABLE IF NOT EXISTS Users(
  username TEXT,
  email TEXT,
  name TEXT,
  password TEXT,
  PRIMARY KEY (username)
);

CREATE TABLE IF NOT EXISTS User_Digimon(
  username TEXT,
  digimon_1 TEXT,
  digimon_2 TEXT,
  digimon_3 TEXT,
  digimon_4 TEXT,
  digimon_5 TEXT,
  digimon_6 TEXT,
  PRIMARY KEY (username),
  FOREIGN KEY (username) REFERENCES Users(username),
  FOREIGN KEY (digimon_1) REFERENCES Digimon(digimon_name),
  FOREIGN KEY (digimon_2) REFERENCES Digimon(digimon_name),
  FOREIGN KEY (digimon_3) REFERENCES Digimon(digimon_name),
  FOREIGN KEY (digimon_4) REFERENCES Digimon(digimon_name),
  FOREIGN KEY (digimon_5) REFERENCES Digimon(digimon_name),
  FOREIGN KEY (digimon_6) REFERENCES Digimon(digimon_name)
);