# Cursor Rules for Vulnerability MCP Server

## Project Context
This project is a web application for managing and monitoring vulnerabilities, built with Python FastAPI and Docker.

## Version Control Rules
1. Always push changes to GitHub immediately after completion
2. Keep only one source of truth (either remote or local)
3. Before making changes:
   - Pull latest changes from remote
   - Ensure local version is up to date
4. After making changes:
   - Commit with meaningful messages
   - Push to remote immediately
   - Verify changes are reflected in remote
5. Never mix remote and local versions without synchronization
6. Document any version conflicts and their resolution
7. Use branches for feature development
8. Merge changes only after testing
9. Keep remote repository as the source of truth
10. Regular synchronization checks between local and remote

## File Structure Rules
1. All application code should be in the `app/` directory
2. Configuration files should be in the root directory
3. Docker-related files should be in the root directory
4. Database migrations should be in the `migrations/` directory
5. Template files must be in `app/templates/` directory
6. Static files must be in `app/static/` directory
7. No duplicate template files in different locations
8. Keep consistent file naming conventions
9. Document file dependencies
10. Maintain clear separation of concerns

## Code Style Rules
1. Python files should follow PEP 8 guidelines
2. Use type hints in Python code
3. Document all functions and classes
4. Use meaningful variable and function names
5. Keep functions focused and single-purpose
6. Validate all form inputs
7. Implement proper error handling
8. Use consistent naming conventions
9. Document API endpoints
10. Include input validation

## Security Rules
1. Never commit sensitive information
2. Use environment variables for secrets
3. Validate all user inputs
4. Implement proper authentication checks
5. Use HTTPS in production
6. Sanitize user inputs
7. Implement CSRF protection
8. Use secure session management
9. Implement rate limiting
10. Regular security audits

## Docker Rules
1. Use multi-stage builds for smaller images
2. Include only necessary files in images
3. Use specific version tags
4. Document all environment variables
5. Follow security best practices
6. Regular image updates
7. Monitor container health
8. Implement proper logging
9. Use health checks
10. Document container dependencies

## Database Rules
1. Use migrations for all schema changes
2. Include rollback procedures
3. Backup data regularly
4. Use parameterized queries
5. Implement proper indexing
6. Document schema changes
7. Regular database maintenance
8. Monitor database performance
9. Implement proper constraints
10. Regular data validation

## Frontend Rules
1. Use semantic HTML
2. Implement responsive design
3. Follow accessibility guidelines
4. Optimize assets
5. Use modern JavaScript features
6. Validate form inputs
7. Implement proper error handling
8. Use consistent styling
9. Document UI components
10. Regular UI/UX testing

## Testing Rules
1. Write unit tests for critical functions
2. Include integration tests
3. Test security features
4. Document test cases
5. Maintain test coverage
6. Test form submissions
7. Test error scenarios
8. Test edge cases
9. Regular regression testing
10. Document test results

## Documentation Rules
1. Keep README.md up to date
2. Document API endpoints
3. Include setup instructions
4. Document deployment process
5. Maintain changelog
6. Document known issues
7. Include troubleshooting guides
8. Document configuration options
9. Maintain API documentation
10. Document security measures

## Git Rules
1. Use meaningful commit messages
2. Create feature branches
3. Review code before merging
4. Keep commits atomic
5. Tag releases
6. Document breaking changes
7. Regular repository maintenance
8. Clean up old branches
9. Document merge conflicts
10. Regular repository backups

## Deployment Rules
1. Use CI/CD pipelines
2. Implement rollback procedures
3. Monitor deployments
4. Test in staging
5. Document deployment process
6. Regular deployment testing
7. Monitor application health
8. Implement logging
9. Document deployment issues
10. Regular deployment reviews

## Remote Server Access
- Server: zabbix
- SSH Command: `ssh -l root zabbix`
- No password required (SSH key authentication)
- Document server changes
- Regular server maintenance
- Monitor server health
- Implement proper logging
- Regular backups
- Document server issues
- Regular security updates

## GitHub Configuration
- Repository: git@github.com:nesirat/Vulnerability-MCP-Server.git
- Branch: main
- Using SSH for authentication
- Regular repository updates
- Document repository changes
- Monitor repository health
- Implement proper access control
- Regular repository backups
- Document repository issues
- Regular security audits

## Recent Issues and Solutions
1. Login/Registration Form Issues:
   - Templates must be in correct directory
   - No duplicate template files
   - Proper form validation
   - Consistent routing
   - Error handling
   - User feedback
   - Session management
   - Security measures
   - Testing procedures
   - Documentation updates

2. File Management:
   - Consistent file locations
   - No duplicate files
   - Proper file permissions
   - Regular file cleanup
   - File dependency checks
   - Version control
   - Backup procedures
   - Documentation
   - Testing
   - Maintenance

3. Database Management:
   - Proper initialization
   - User creation
   - Schema validation
   - Data integrity
   - Backup procedures
   - Error handling
   - Monitoring
   - Documentation
   - Testing
   - Maintenance

## Project Structure
- Main application code in `main.py`
- Docker configuration in `docker-compose.yml`
- Database configuration in `database.py`
- Installation script in `install.py`
- Requirements in `requirements.txt`

## Development Guidelines
- Use SSH for Git operations
- Keep sensitive information in environment variables
- Follow PEP 8 style guide
- Document all major changes
- Test changes locally before deployment

## Deployment Process
1. Make changes locally
2. Test changes
3. Commit and push to GitHub
4. Deploy to remote server using SSH
5. Run installation script if needed

## Security Guidelines
- Use SSH keys for authentication
- Keep credentials secure
- Use environment variables for sensitive data
- Regular security updates
- Follow security best practices

## Maintenance
- Regular backups
- Monitor logs
- Update dependencies
- Check system health
- Document changes

## Installation Documentation
1. Document all manual installation steps
2. Note any system-specific requirements
3. Record package versions and dependencies
4. Document any configuration changes
5. Keep track of environment variables
6. Note any security considerations
7. Document troubleshooting steps
8. Record successful installation patterns
9. Note any system-specific commands
10. Document all manual interventions

## Manual Installation Log
### Docker Installation (2024-03-21)
- Required packages:
  - docker.io
  - docker-compose
- Installation steps:
  1. Update package list: `apt-get update`
  2. Install Docker: `apt-get install -y docker.io`
  3. Install Docker Compose: `apt-get install -y docker-compose`
  4. Start Docker service: `systemctl start docker`
  5. Enable Docker service: `systemctl enable docker`
- Verification:
  - Check Docker version: `docker --version`
  - Check Docker Compose version: `docker-compose --version`
  - Verify Docker service: `systemctl status docker` 