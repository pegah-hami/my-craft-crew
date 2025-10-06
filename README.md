# Multi-Agent Design System

A scalable multi-agent system for generating product designs and collages using Python, FastAPI, and Pillow.

## Features

- **Multi-Agent Architecture**: Coordinated agents for different design tasks
- **Image Processing**: Advanced image manipulation using Pillow
- **Collage Generation**: Multiple layout algorithms (grid, stacked, circular, freeform, mosaic)
- **REST API**: FastAPI-based API for easy integration
- **Async Processing**: Background task processing for better performance
- **Extensible Design**: Easy to add new agents and capabilities
- **Future-Ready**: Architecture prepared for Hugging Face integration

## Architecture

### Core Components

- **Coordinator Agent**: Central orchestrator for task management and agent communication
- **Design Agent**: Specialized agent for collage generation and image processing
- **Image Processor**: Service for image manipulation and optimization
- **Collage Generator**: Service for creating various collage layouts
- **File Manager**: Service for handling file uploads and storage

### Agent Types

- **Design Agent**: Handles collage generation and image processing
- **Effects Agent**: (Future) Image effects and filters
- **Optimization Agent**: (Future) File optimization and compression
- **Hugging Face Agent**: (Future) AI-powered image generation

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd multi_agent_design_system
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create necessary directories**:
   ```bash
   mkdir -p uploads processed_images collages logs temp
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## API Documentation

### Endpoints

- **POST** `/api/v1/upload/images` - Upload multiple images
- **POST** `/api/v1/design/generate` - Generate design with specific parameters
- **GET** `/api/v1/task/{task_id}` - Get task status
- **GET** `/api/v1/task/{task_id}/result` - Download completed design
- **DELETE** `/api/v1/task/{task_id}` - Cancel a task
- **GET** `/api/v1/tasks` - List tasks with filtering
- **GET** `/api/v1/agents/status` - Get agent status
- **GET** `/api/v1/storage/stats` - Get storage statistics
- **POST** `/api/v1/storage/cleanup` - Clean up old files

### Interactive API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Usage Examples

### Upload Images and Generate Collage

```python
import requests

# Upload images
files = [
    ('files', open('image1.jpg', 'rb')),
    ('files', open('image2.jpg', 'rb')),
    ('files', open('image3.jpg', 'rb'))
]

response = requests.post(
    'http://localhost:8000/api/v1/upload/images',
    files=files
)

task_id = response.json()['task_id']

# Check task status
status_response = requests.get(f'http://localhost:8000/api/v1/task/{task_id}')
print(status_response.json())

# Download result when completed
if status_response.json()['task']['status'] == 'completed':
    result_response = requests.get(f'http://localhost:8000/api/v1/task/{task_id}/result')
    with open('collage.jpg', 'wb') as f:
        f.write(result_response.content)
```

### Generate Design with Custom Parameters

```python
import requests

# Define design parameters
design_data = {
    "images": [
        {"id": "image1", "file_path": "/path/to/image1.jpg"},
        {"id": "image2", "file_path": "/path/to/image2.jpg"}
    ],
    "layout": "grid",
    "output_width": 1920,
    "output_height": 1080,
    "background_color": "#FFFFFF",
    "spacing": 20
}

response = requests.post(
    'http://localhost:8000/api/v1/design/generate',
    json=design_data
)

task_id = response.json()['task']['id']
```

## Configuration

### Environment Variables

- `APP_NAME`: Application name (default: "Multi-Agent Design System")
- `DEBUG`: Enable debug mode (default: False)
- `LOG_LEVEL`: Logging level (default: "INFO")
- `HOST`: Server host (default: "0.0.0.0")
- `PORT`: Server port (default: 8000)
- `UPLOAD_DIRECTORY`: Directory for uploaded files (default: "uploads")
- `MAX_FILE_SIZE_MB`: Maximum file size in MB (default: 10)
- `DEFAULT_IMAGE_QUALITY`: Default image quality (default: 95)
- `MAX_CONCURRENT_TASKS_PER_AGENT`: Max tasks per agent (default: 3)

### Configuration File

Create a `.env` file in the project root:

```env
DEBUG=True
LOG_LEVEL=DEBUG
HOST=0.0.0.0
PORT=8000
UPLOAD_DIRECTORY=uploads
MAX_FILE_SIZE_MB=10
DEFAULT_IMAGE_QUALITY=95
```

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

## Collage Layouts

### Grid Layout
- Arranges images in a grid pattern
- Automatically calculates optimal cell sizes
- Supports any number of images

### Stacked Layout
- Arranges images vertically
- Each image takes equal height
- Good for vertical compositions

### Circular Layout
- Arranges images in a circle
- Images positioned around a central point
- Creates dynamic compositions

### Freeform Layout
- Random placement of images
- Avoids overlapping
- Creates artistic, organic layouts

### Mosaic Layout
- Small tiles arranged in pattern
- Creates mosaic-like effects
- Good for many small images

## Future Enhancements

### Planned Features

1. **Hugging Face Integration**
   - Text-to-image generation
   - Style transfer
   - Background generation
   - Object inpainting

2. **Effects Agent**
   - Filter application
   - Color adjustment
   - Blur effects
   - Sharpening

3. **Optimization Agent**
   - File size optimization
   - Quality optimization
   - Format conversion
   - Batch processing

4. **Database Integration**
   - Task persistence
   - User management
   - Performance metrics

5. **Advanced Features**
   - Real-time collaboration
   - Template system
   - Batch processing
   - API rate limiting

## Development

### Project Structure

```
multi_agent_design_system/
├── agents/                 # Agent implementations
│   ├── base_agent.py      # Abstract base agent
│   ├── design_agent.py    # Design generation agent
│   └── future_agents/     # Placeholder for future agents
├── api/                   # FastAPI routes and middleware
│   ├── routes.py          # API endpoints
│   └── middleware.py      # Request/response middleware
├── config/                 # Configuration management
│   ├── settings.py        # Application settings
│   └── agent_configs.py   # Agent configuration templates
├── models/                 # Data models
│   ├── task_models.py     # Task and agent models
│   └── design_models.py   # Design-specific models
├── services/               # Business logic services
│   ├── image_processor.py  # Image processing service
│   ├── collage_generator.py # Collage generation service
│   └── file_manager.py    # File management service
├── coordinator/           # Coordinator agent (future)
├── utils/                 # Utility functions
├── tests/                 # Test files
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

### Adding New Agents

1. **Create Agent Class**:
   ```python
   from ..agents.base_agent import BaseAgent
   from ..models.task_models import AgentType
   
   class NewAgent(BaseAgent):
       def __init__(self, agent_id: str):
           super().__init__(
               agent_id=agent_id,
               agent_type=AgentType.NEW_TYPE,
               capabilities=["capability1", "capability2"],
               max_concurrent_tasks=2
           )
       
       async def validate_task(self, task: Task) -> bool:
           # Implement validation logic
           pass
       
       async def process_task(self, task: Task) -> Dict[str, Any]:
           # Implement processing logic
           pass
   ```

2. **Register Agent**:
   ```python
   from ..config.agent_configs import agent_registry
   
   agent_config = agent_registry.create_from_template(
       agent_id="new_agent_001",
       template_type="new_type"
   )
   ```

3. **Add to Main Application**:
   ```python
   # In main.py
   new_agent = NewAgent("new_agent_001")
   await new_agent.start()
   app.state.new_agent = new_agent
   ```

### Testing

Run tests with pytest:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest --cov=. tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support:

- Create an issue on GitHub
- Check the API documentation at `/docs`
- Review the configuration options

## Changelog

### v0.1.0
- Initial release
- Basic multi-agent architecture
- Image upload and processing
- Collage generation with multiple layouts
- REST API with FastAPI
- Pillow-based image processing
- Extensible agent system
