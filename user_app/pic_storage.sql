SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

CREATE SCHEMA IF NOT EXISTS `pic_Storage` DEFAULT CHARACTER SET latin1 ;
USE `pic_Storage` ;


-- -----------------------------------------------------
-- Table `Pic_Storage`.`users`
-- -----------------------------------------------------

DROP TABLE IF EXISTS `pic_Storage`.`users` ;

CREATE TABLE IF NOT EXISTS `pic_Storage`.`users` (
  `user_id` INT NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(100) UNIQUE NOT NULL,
  `password` VARCHAR(300) NOT NULL,
  `created at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`))
  
ENGINE = MyISAM
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `Pic_Storage`.`uploads`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `pic_Storage`.`uploads` ;

CREATE TABLE IF NOT EXISTS `pic_Storage`.`uploads` (
  `photo_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT NOT NULL,
  `file_name` VARCHAR(300) UNIQUE NOT NULL,
  `ori_path` VARCHAR(300) NOT NULL,
  `text_path` VARCHAR(300) NOT NULL,
  `thumb_path` VARCHAR(300) NOT NULL,
  `created at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`photo_id`)
  )

  ENGINE = InnoDB;
  

  -- -----------------------------------------------------
-- Table `Pic_Storage`.`uploads`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `pic_Storage`.`auto_scaler` ;

CREATE TABLE IF NOT EXISTS `pic_Storage`.`auto_scaler` (
  `auto_id` INT NOT NULL AUTO_INCREMENT,
  `cpu_grow` INT NOT NULL,
  `cpu_shrink` INT NOT NULL,
  `grow_ratio` INT NOT NULL,
  `shrink_ratio` INT NOT NULL,
  PRIMARY KEY (`auto_id`)
  )
  ENGINE = InnoDB;

commit;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;