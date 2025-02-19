from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, and_
from db import LamodaItem
from argparse import ArgumentParser
import os 



if __name__ == '__main__':
    #arg_parser = ArgumentParser()
    #arg_parser.add_argument('-d', '--dir', type=str, help='Путь к файлу sqlite')
    #args = arg_parser.parse_args()
    #engine = create_engine(f"sqlite:///{args.dir}")
    engine = create_engine(f"sqlite:///./output/output_1734098285331/db.sqlite3")
    dup_count = 0
    with Session(engine) as session:
        '''all_items = session.query(LamodaItem).all()
        for item in all_items:
            item.img_rel_path = str(item.img_rel_path).replace(os.sep, '/')
        session.commit()'''
        #print(f'Всего объектов в базе {len(all_items)}')
        #dups = session.query(LamodaItem).having(func.count(LamodaItem.img_rel_path) > 1).group_by(LamodaItem.img_rel_path).all()
        subq = (
            session.query(LamodaItem.img_rel_path, func.min(LamodaItem.id).label("min_id")).group_by(LamodaItem.img_rel_path)
            ).subquery('pth_min_id')
        q_duplicates = (session.query(LamodaItem).join(subq, and_(
            LamodaItem.img_rel_path == subq.c.img_rel_path, LamodaItem.id != subq.c.min_id)
            ))

        for item in q_duplicates:
            #session.delete(item)
            dup_count += 1
            print(item.img_rel_path)

        for item in q_duplicates:
            session.delete(item)
            dup_count += 1
        session.commit()

        print(f'Было удалено {dup_count} записей')
        

