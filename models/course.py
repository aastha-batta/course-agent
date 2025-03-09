from typing import List, Dict, Any, Optional
from datetime import datetime
import json

class Lesson:
    """Represents a single lesson in a course module"""
    
    def __init__(self, title: str, description: str, content: str = "", resources: List[str] = None):
        self.title = title
        self.description = description
        self.content = content
        self.resources = resources or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "resources": self.resources
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Lesson':
        """Create a Lesson object from dictionary data"""
        return cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            content=data.get("content", ""),
            resources=data.get("resources", [])
        )


class Module:
    """Represents a module in a course"""
    
    def __init__(self, title: str, description: str = "", lessons: List[Lesson] = None, duration: str = "1 week"):
        self.title = title
        self.description = description
        self.lessons = lessons or []
        self.duration = duration
    
    def add_lesson(self, lesson: Lesson) -> None:
        """Add a lesson to this module"""
        self.lessons.append(lesson)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "title": self.title,
            "description": self.description,
            "lessons": [lesson.to_dict() for lesson in self.lessons],
            "duration": self.duration
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Module':
        """Create a Module object from dictionary data"""
        module = cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            duration=data.get("duration", "1 week")
        )
        
        for lesson_data in data.get("lessons", []):
            module.add_lesson(Lesson.from_dict(lesson_data))
            
        return module


class Course:
    """Represents a complete educational course"""
    
    def __init__(self, 
                 title: str, 
                 description: str, 
                 topic: str,
                 depth: str = "intermediate",
                 course_duration: str = "6 weeks",
                 modules: List[Module] = None,
                 references: List[str] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self.title = title
        self.description = description
        self.topic = topic
        self.depth = depth
        self.course_duration = course_duration
        self.modules = modules or []
        self.references = references or []
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.validation_results = {}
    
    def add_module(self, module: Module) -> None:
        """Add a module to this course"""
        self.modules.append(module)
    
    def add_reference(self, reference: str) -> None:
        """Add a reference to this course"""
        self.references.append(reference)
        
    def get_duration_in_weeks(self) -> int:
        """Extract the number of weeks from the course duration"""
        try:
            return int(self.course_duration.split()[0])
        except (ValueError, IndexError, AttributeError):
            return len(self.modules)
    
    def adjust_modules_to_duration(self) -> None:
        """Adjust the number of modules to match the specified duration"""
        num_weeks = self.get_duration_in_weeks()
        if len(self.modules) > num_weeks:
            self.modules = self.modules[:num_weeks]
        elif len(self.modules) < num_weeks:
            # Add empty modules to reach the desired duration
            for i in range(len(self.modules), num_weeks):
                self.add_module(Module(f"Module {i+1}", "Content to be developed"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "title": self.title,
            "description": self.description,
            "topic": self.topic,
            "depth": self.depth,
            "course_duration": self.course_duration,
            "modules": [module.to_dict() for module in self.modules],
            "references": self.references,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "validation_results": self.validation_results
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Course':
        """Create a Course object from dictionary data"""
        course = cls(
            title=data.get("title", data.get("course_title", "")),  
            description=data.get("description", ""),
            topic=data.get("topic", ""),
            depth=data.get("depth", "intermediate"),
            course_duration=data.get("course_duration", "6 weeks"),
            references=data.get("references", []) or []  
        )
        
        if "created_at" in data:
            try:
                course.created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                pass
                
        if "updated_at" in data:
            try:
                course.updated_at = datetime.fromisoformat(data["updated_at"])
            except (ValueError, TypeError):
                pass
        
        if "validation_results" in data:
            course.validation_results = data["validation_results"]
        
        modules_data = data.get("modules", [])
        if modules_data is None: 
            modules_data = []
        for module_data in modules_data:
            course.add_module(Module.from_dict(module_data))
            
        return course
    
    def __str__(self):
        """Readable string representation of the course"""
        return f"Course(title={self.title}, modules={len(self.modules)}, duration={self.course_duration}, topic={self.topic})"

    def __repr__(self):
        """Return a detailed JSON string representation"""
        return json.dumps(self.to_dict(), indent=2)