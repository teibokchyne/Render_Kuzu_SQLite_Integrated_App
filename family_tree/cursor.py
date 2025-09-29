from flask import current_app as app

class Cursor:
    def query(self, db, table, *args, filter_by=False, **kwargs):
        """
        Query a SQLAlchemy table with either filter() or filter_by().

        Parameters:
        - db: The SQLAlchemy instance (usually `from yourapp import db`)
        - table: The SQLAlchemy model (e.g. User, Order)
        - *args: Positional filter expressions (for .filter())
        - filter_by: If True, use filter_by(**kwargs); otherwise use filter(*args)
        - **kwargs: Keyword filter arguments (used only if filter_by=True)

        Returns:
        - A query object you can call .all(), .first(), etc.
        """

        if filter_by:
            return db.session.query(table).filter_by(**kwargs)
        elif args and kwargs:
            return db.session.query(table).filter(*args).filter_by(**kwargs)
        elif args:
            return db.session.query(table).filter(*args)
        else:
            return db.session.query(table)
        
    
    def add(self, db, table, **kwargs):
        """
        Add a new record to a SQLAlchemy table.

        Parameters:
            db: The SQLAlchemy instance (usually `from yourapp import db`)
            table: The SQLAlchemy model class to instantiate (e.g. User, Order)
            **kwargs: Field values for the new record (passed to model constructor)

        Commits the new record to the database.
        """
        new_record = table(**kwargs)
        db.session.add(new_record)
        db.session.commit()

    def update(self, db, table, record_id, **kwargs):
        """
        Update an existing record in a SQLAlchemy table.

        Parameters:
            db: The SQLAlchemy instance (usually `from yourapp import db`)
            table: The SQLAlchemy model class (e.g. User, Order)
            record_id: The primary key of the record to update
            **kwargs: Field values to update (passed to model instance)
        """
        record = db.session.query(table).filter_by(id=record_id).first()
        if not record:
            raise ValueError(f"Record with id {record_id} not found in {table.__tablename__}")
        for key, value in kwargs.items():
            setattr(record, key, value)
        db.session.commit()

    def delete(self, db, table, **kwargs):
        """
        Delete a record from a SQLAlchemy table.

        Parameters:
            db: The SQLAlchemy instance (usually `from yourapp import db`)
            table: The SQLAlchemy model class (e.g. User, Order)
            record_id: The primary key of the record to delete
        """
        records = db.session.query(table).filter_by(**kwargs).all()
        if not records:
            app.logger.warning(f"No records found in {table.__tablename__} matching {kwargs}")
        for record in records:
            db.session.delete(record)
        db.session.commit()
