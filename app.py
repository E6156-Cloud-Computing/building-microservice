from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, Boolean, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column
import googlemaps

def serialize_doc(doc):
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://root:oyyb980219@localhost:3306/db'

app.config["GOOGLE_MAPS_API_KEY"] = "AIzaSyChRU-WeMzdOJPcJh34tnz-YWTr3vNJt08"
gmaps = googlemaps.Client(key=app.config["GOOGLE_MAPS_API_KEY"])


class Base(DeclarativeBase):
  pass

db = SQLAlchemy(app, model_class=Base)

class Building(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    building_name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(100))
    num_floor: Mapped[int] = mapped_column(Integer)

class Rooms_Building(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_type: Mapped[str] = mapped_column(String(20))
    available: Mapped[bool] = mapped_column(Boolean)
    room_number: Mapped[int] = mapped_column(Integer, unique=True)
    building_id: Mapped[int] = mapped_column(Integer, ForeignKey('building.id'), index=True)

with app.app_context():
    db.create_all()

    building = db.session.execute(db.select(Building)).scalars()
    print(building)

@app.route('/get_location', methods=['GET'])
def get_location():
    address = request.args.get("address")
    if not address:
        return jsonify({"error": "Address is required"}), 400

    geocode_result = gmaps.geocode(address)
    if geocode_result:
        return jsonify(geocode_result[0]['geometry']['location'])
    else:
        return jsonify({"error": "Location not found"}), 404



@app.route('/api/building', methods=['GET'])
def get_buildings():
    building_info = db.session.query(Building).all()
    buildings_list = [{'id': b.id, 'building_name': b.building_name, 'description': b.description, 'num_floor': b.num_floor} for b in building_info]

    if building_info:
        return jsonify({"message": "successfully", "content": buildings_list}), 201
    else:
        return jsonify({"error": "Building info not found"}), 404

@app.route('/api/building', methods=['POST'])
def create_building():
    data = request.json
    building_name = data['building_name']
    description = data.get('description', "")
    num_floor = data.get('num_floor', 6)

    if building_name:
        if num_floor>0:
            new_building = Building(building_name=building_name, description=description, num_floor=num_floor)
            db.session.add(new_building)
            db.session.commit()
            building_dict = {
                'id': new_building.id,
                'building_name': new_building.building_name,
                'description': new_building.description,
                'num_floor': new_building.num_floor
            }
            return jsonify({"message": "Building info inserted successfully", "content": building_dict}), 201
        else:
            return jsonify({"message": "Invalid value for building floor"}), 500
    else:
        return jsonify({"message": "Missing Building name"}), 500

@app.route('/api/building/<string:building_name>', methods=['GET'])
def get_building(building_name):
    building_info = db.session.query(Building).filter_by(building_name=building_name)
    buildings_list = [{'id': b.id, 'building_name': b.building_name, 'description': b.description, 'num_floor': b.num_floor} for b in building_info]

    if building_info:
        return jsonify({"message": "successfully", "content": buildings_list}), 201
    else:
        return jsonify({"error": "Building info not found"}), 404

@app.route('/api/building/<string:building_name>', methods=['PUT'])
def update_building(building_name):
    building_info = db.session.query(Building).filter_by(building_name=building_name).first()

    if building_info:
        data = request.get_json(force=True)
        building_info.building_name = data.get('building_name', building_info.building_name)
        building_info.description = data.get('description', building_info.description)
        building_info.num_floor = data.get('num_floor', building_info.num_floor)

        db.session.commit()

        building_dict = {'id': building_info.id, 'building_name': building_info.building_name, 'description': building_info.description, 'num_floor': building_info.num_floor}
        return jsonify({"message": "Building info updated successfully", "content": building_dict}), 201
    else:
        return jsonify({"error": "Building info not found"}), 404

@app.route('/api/building/<string:building_name>', methods=['DELETE'])
def delete_building(building_name):
    building_info = db.session.query(Building).filter_by(building_name=building_name).first()

    if building_info:
        db.session.delete(building_info)
        db.session.commit()
        return jsonify({"message": "Building info deleted successfully"}), 200
    else:
        return jsonify({"error": "Building info not found"}), 404

@app.route("/api/building/<string:building_name>/room/<string:room_type>", methods=['POST'])
def create_room(building_name, room_type):
    building_info = db.session.query(Building).filter_by(building_name=building_name).first()
    data = request.get_json(force=True)
    building_name = data['building_name']
    room_number = data.get('room_number', 0)
    room_type = data.get('room_type', "")
    available = data.get('available', False)
    
    if building_info:
        existing_room = db.session.query(Rooms_Building).filter_by(building_id=building_info.id, room_number=room_number).first()
        if existing_room:
            return jsonify({"message": "Room number already exist"}), 500
        if room_number>0 and room_type:
            new_room = Rooms_Building(room_number=room_number, room_type=room_type, available=available, building_id=building_info.id)
            db.session.add(new_room)
            db.session.commit()
            room_dict = {
                'id': new_room.id,
                'room_number': new_room.room_number,
                'room_type': new_room.room_type,
                'available': new_room.available,
                'building_id': new_room.building_id
            }
            return jsonify({"message": "Room info inserted successfully", "content": room_dict}), 201
        else:
            return jsonify({"message": "Invalid value for room info"}), 500
    else:
        return jsonify({"message": "Building info not found"}), 500

@app.route('/api/building/<string:building_name>/room/<string:room_type>', methods=['GET'])
def get_room_info(building_name, room_type):
    building_info = db.session.query(Building).filter_by(building_name=building_name).first()

    if building_info:
        rooms = db.session.query(Rooms_Building).filter_by(building_id=building_info.id, room_type=room_type).all()
        rooms_list = [{'id': room.id, 'room_number': room.room_number, 'room_type': room.room_type, 'available': room.available, 'building_id': room.building_id} for room in rooms]
        return jsonify({"message": f"Rooms for {building_name}", "content": rooms_list}), 200
    else:
        return jsonify({"error": "Building info not found"}), 404
    
@app.route('/api/building/<string:building_name>/room/<string:room_type>/<int:room_number>', methods=['PUT'])
def update_room_info(building_name, room_type, room_number):
    building_info = db.session.query(Building).filter_by(building_name=building_name).first()
    
    if building_info:
        room_info = db.session.query(Rooms_Building).filter_by(building_id=building_info.id, room_type=room_type, room_number=room_number).first()
        data = request.get_json(force=True)
        room_info.room_type = data.get('room_type', room_info.room_type)
        room_info.room_number = data.get('room_number', room_info.room_number)
        room_info.available = data.get('available', room_info.available)  
        db.session.commit()

        room_dict = {'id': room_info.id, 'room_type': room_info.room_type, 'available': room_info.available, 'room_number': room_info.room_number, 'building_id': room_info.building_id}
        return jsonify({"message": "Building info updated successfully", "content": room_dict}), 201
    else:
        return jsonify({"error": "Building info not found"}), 404
    
@app.route('/api/building/<string:building_name>/room/<string:room_type>/<int:room_number>', methods=['DELETE'])
def delete_room(building_name, room_type, room_number):
    building_info = db.session.query(Building).filter_by(building_name=building_name).first()
    room_info = db.session.query(Rooms_Building).filter_by(building_id=building_info.id, room_type=room_type, room_number=room_number).first()

    if building_info:
        if room_info:
            db.session.delete(room_info)
            db.session.commit()
            return jsonify({"message": "Room info deleted successfully"}), 200
        else:
            return jsonify({"error": "Room info not found"}), 404
    else:
        return jsonify({"error": "Building info not found"}), 404


if __name__ == '__main__':
    app.run(debug=True)