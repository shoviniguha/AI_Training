>use teachers
<switched to db teachers

>db.teachers.insertMany([{teacher_id:1, name: "Rahul", age: 65, course:"AI"},
		       {teacher_id:2, name: "Megha", age: 34, course:"ML"},
		       {teacher_id:3, name: "Arun", age: 49, course:"DBMS"},
		       {teacher_id:4, name: "Nehal", age: 38, course:"Data Science"},
           {teacher_id:5, name: "Nakul", age: 55, course:"AI"}
<{
  acknowledged: true,
  insertedIds: {
    '0': ObjectId('68dfb5189ed9d454bb5d3d84'),
    '1': ObjectId('68dfb5189ed9d454bb5d3d85'),
    '2': ObjectId('68dfb5189ed9d454bb5d3d86'),
    '3': ObjectId('68dfb5189ed9d454bb5d3d87'),
    '4': ObjectId('68dfb5189ed9d454bb5d3d88')
  }
}

>// Find all teachers
db.teachers.find()
<{
  _id: ObjectId('68dfb5189ed9d454bb5d3d84'),
  teacher_id: 1,
  name: 'Rahul',
  age: 65,
  course: 'AI'
}
{
  _id: ObjectId('68dfb5189ed9d454bb5d3d85'),
  teacher_id: 2,
  name: 'Megha',
  age: 34,
  course: 'ML'
}
{
  _id: ObjectId('68dfb5189ed9d454bb5d3d86'),
  teacher_id: 3,
  name: 'Arun',
  age: 49,
  course: 'DBMS'
}
{
  _id: ObjectId('68dfb5189ed9d454bb5d3d87'),
  teacher_id: 4,
  name: 'Nehal',
  age: 38,
  course: 'Data Science'
}
{
  _id: ObjectId('68dfb5189ed9d454bb5d3d88'),
  teacher_id: 5,
  name: 'Nakul',
  age: 55,
  course: 'AI'
}

>// Find one teacher
db.teachers.findOne({name:"Rahul"})
<{
  _id: ObjectId('68dfb5189ed9d454bb5d3d84'),
  teacher_id: 1,
  name: 'Rahul',
  age: 65,
  course: 'AI'
}

>// Find students with age greater than 40
db.teachers.find({age:{$gt:40}})
<{
  _id: ObjectId('68dfb5189ed9d454bb5d3d84'),
  teacher_id: 1,
  name: 'Rahul',
  age: 65,
  course: 'AI'
}
{
  _id: ObjectId('68dfb5189ed9d454bb5d3d86'),
  teacher_id: 3,
  name: 'Arun',
  age: 49,
  course: 'DBMS'
}
{
  _id: ObjectId('68dfb5189ed9d454bb5d3d88'),
  teacher_id: 5,
  name: 'Nakul',
  age: 55,
  course: 'AI'
}

>// Display only name and course(Projection)
<db.teachers.find({},{name: 1,course: 1, _id: 0})
{
  name: 'Rahul',
  course: 'AI'
}
{
  name: 'Megha',
  course: 'ML'
}
{
  name: 'Arun',
  course: 'DBMS'
}
{
  name: 'Nehal',
  course: 'Data Science'
}
{
  name: 'Nakul',
  course: 'AI'
}

>// Update one teacher's age and course
<db.students.updateOne(
{name:'Nehal'},
{$set:{age: 39, course: 'Advanced AI'}}
)
{
  acknowledged: true,
  insertedId: null,
  matchedCount: 0,
  modifiedCount: 0,
  upsertedCount: 0
}

>// Delete one record
db.teachers.deleteOne({name:'Nehal'})
<{
  acknowledged: true,
  deletedCount: 1
}

>// Delete all teachers over the age of 60
db.teachers.deleteMany({age:{$gt:60}})
<{
  acknowledged: true,
  deletedCount: 1
}